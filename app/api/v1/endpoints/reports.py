import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL
from app.db.session import get_db
from app.models.indicator import Indicator
from app.models.score_student import ScoreStudent
from app.models.report import Report
from app.models.report_indicator import ReportIndicator
from app.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    IndicatorAnalysis,
    ImprovementSuggestion,
    ReportSaveRequest,
    ReportSaveResponse,
    ReportGetResponse,
    SavedIndicatorAnalysis,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_LEVEL_THRESHOLDS = {"H": 0.5, "L": -0.5}


def _score_to_level(score: float) -> str:
    if score >= _LEVEL_THRESHOLDS["H"]:
        return "H"
    if score <= _LEVEL_THRESHOLDS["L"]:
        return "L"
    return "M"


def _build_prompt(
    top3: List[dict],
    bottom3: List[dict],
) -> str:
    strengths_text = "\n".join(
        f"- {item['name']}（标准化得分: {item['score']:.2f}, 等级: {item['level']}）"
        for item in top3
    )
    weaknesses_text = "\n".join(
        f"- {item['name']}（标准化得分: {item['score']:.2f}, 等级: {item['level']}）"
        for item in bottom3
    )

    return f"""你是一位专业的学生心理测评报告撰写专家。请根据以下学生的心理测评指标得分，生成个性化分析报告内容。

【优势指标（得分最高的三项）】
{strengths_text}

【不足指标（得分最低的三项）】
{weaknesses_text}

请严格按照以下 JSON 格式输出，不要输出任何 JSON 以外的内容：

{{
  "strengths_analysis": [
    {{
      "indicator_name": "<指标名称>",
      "analysis": "<针对该指标写一段温暖、具体、有洞察力的解释，100-150字，用第二人称"你">"
    }}
  ],
  "weaknesses_analysis": [
    {{
      "indicator_name": "<指标名称>",
      "analysis": "<针对该指标写一段客观、有建设性的分析，100-150字，用第二人称"你">"
    }}
  ],
  "improvement_suggestions": [
    {{
      "indicator_name": "<指标名称>",
      "suggestion": "<针对该不足指标给出一条具体可操作的改进建议，50-80字>"
    }}
  ]
}}

要求：
1. strengths_analysis 必须包含 3 条，对应三个优势指标，顺序与输入一致
2. weaknesses_analysis 必须包含 3 条，对应三个不足指标，顺序与输入一致
3. improvement_suggestions 必须包含 3 条，对应三个不足指标，顺序与输入一致
4. 语言风格：温暖、专业、贴近学生，避免说教感
5. 只输出合法 JSON，不要有任何多余文字"""


@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
) -> ReportGenerateResponse:
    """
    为指定学生生成个性化报告的三、四、五部分：
    - 三、具体指标优势项分析（得分最高的三项）
    - 四、具体指标不足分析（得分最低的三项）
    - 五、针对性改进建议（针对最低三项各一条）
    """
    if not QWEN_API_KEY:
        raise HTTPException(status_code=500, detail="QWEN_API_KEY 未配置")

    # 1. 取该学生在该次考试的所有指标得分，JOIN indicator 获取名称
    rows = (
        db.query(ScoreStudent, Indicator)
        .join(Indicator, ScoreStudent.indicator_id == Indicator.id)
        .filter(
            ScoreStudent.student_id == payload.student_id,
            ScoreStudent.exam_id == payload.exam_id,
        )
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 student_id={payload.student_id}, exam_id={payload.exam_id} 的得分数据，请先调用 /scores/compute",
        )

    # 2. 排序，取 top3 / bottom3
    scored = sorted(
        [
            {
                "name": indicator.name,
                "score": score.score_standardized,
                "level": _score_to_level(score.score_standardized),
            }
            for score, indicator in rows
            if score.score_standardized is not None
        ],
        key=lambda x: x["score"],
        reverse=True,
    )

    if len(scored) < 3:
        raise HTTPException(
            status_code=422,
            detail="有效指标得分不足3项，无法生成报告",
        )

    top3 = scored[:3]
    bottom3 = scored[-3:][::-1]  # 最低三项，从低到高排列

    # 3. 调用 Qwen
    try:
        client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的学生心理测评报告撰写专家，擅长将测评数据转化为温暖、个性化的文字分析。",
                },
                {"role": "user", "content": _build_prompt(top3, bottom3)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用 Qwen API 失败: {str(e)}")

    # 4. 解析响应
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"解析 Qwen 响应失败: {str(e)}")

    # 5. 组装返回值（将 LLM 输出与本地得分/等级合并）
    top3_map = {item["name"]: item for item in top3}
    bottom3_map = {item["name"]: item for item in bottom3}

    strengths = []
    for item in data.get("strengths_analysis", []):
        name = item["indicator_name"]
        meta = top3_map.get(name, top3[len(strengths)] if len(strengths) < len(top3) else {})
        strengths.append(
            IndicatorAnalysis(
                indicator_name=name,
                score_standardized=meta.get("score", 0.0),
                level=meta.get("level", "H"),
                analysis=item["analysis"],
            )
        )

    weaknesses = []
    for item in data.get("weaknesses_analysis", []):
        name = item["indicator_name"]
        meta = bottom3_map.get(name, bottom3[len(weaknesses)] if len(weaknesses) < len(bottom3) else {})
        weaknesses.append(
            IndicatorAnalysis(
                indicator_name=name,
                score_standardized=meta.get("score", 0.0),
                level=meta.get("level", "L"),
                analysis=item["analysis"],
            )
        )

    suggestions = [
        ImprovementSuggestion(
            indicator_name=item["indicator_name"],
            suggestion=item["suggestion"],
        )
        for item in data.get("improvement_suggestions", [])
    ]

    return ReportGenerateResponse(
        student_id=payload.student_id,
        exam_id=payload.exam_id,
        strengths_analysis=strengths,
        weaknesses_analysis=weaknesses,
        improvement_suggestions=suggestions,
    )


@router.post("/save", response_model=ReportSaveResponse)
def save_report(payload: ReportSaveRequest, db: Session = Depends(get_db)):
    # 构建 indicator_name -> indicator_id 映射
    indicator_names = (
        [a.indicator_name for a in payload.strengths_analysis]
        + [a.indicator_name for a in payload.weaknesses_analysis]
    )
    indicators = db.query(Indicator).filter(Indicator.name.in_(indicator_names)).all()
    name_to_id = {ind.name: ind.id for ind in indicators}

    # 建立 suggestion 映射
    suggestion_map = {s.indicator_name: s.suggestion for s in payload.improvement_suggestions}

    try:
        with db.begin_nested():
            # 幂等：删除旧报告
            old_report = (
                db.query(Report)
                .filter(Report.student_id == payload.student_id, Report.release == payload.exam_id)
                .first()
            )
            if old_report:
                db.query(ReportIndicator).filter(ReportIndicator.report_id == old_report.id).delete(
                    synchronize_session=False
                )
                db.delete(old_report)
                db.flush()

            report = Report(student_id=payload.student_id, release=payload.exam_id)
            db.add(report)
            db.flush()

            rows: list[ReportIndicator] = []
            for item in payload.strengths_analysis:
                ind_id = name_to_id.get(item.indicator_name)
                rows.append(
                    ReportIndicator(
                        report_id=report.id,
                        indicator_id=ind_id,
                        analysis=item.analysis,
                        suggestion=None,
                        is_positive=True,
                    )
                )
            for item in payload.weaknesses_analysis:
                ind_id = name_to_id.get(item.indicator_name)
                rows.append(
                    ReportIndicator(
                        report_id=report.id,
                        indicator_id=ind_id,
                        analysis=item.analysis,
                        suggestion=suggestion_map.get(item.indicator_name),
                        is_positive=False,
                    )
                )
            db.add_all(rows)

        saved = [
            SavedIndicatorAnalysis(
                indicator_id=r.indicator_id,
                indicator_name=next((n for n, i in name_to_id.items() if i == r.indicator_id), ""),
                analysis=r.analysis,
                suggestion=r.suggestion,
                is_positive=r.is_positive,
            )
            for r in rows
        ]
        return ReportSaveResponse(
            report_id=report.id,
            student_id=payload.student_id,
            exam_id=payload.exam_id,
            indicators=saved,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": "保存报告失败", "error": str(e)})


@router.get("/student/{student_id}", response_model=ReportGetResponse)
def get_report(student_id: int, exam_id: int, db: Session = Depends(get_db)):
    report = (
        db.query(Report)
        .filter(Report.student_id == student_id, Report.release == exam_id)
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 student_id={student_id}, exam_id={exam_id} 的报告，请先调用 /reports/save",
        )

    rows = (
        db.query(ReportIndicator, Indicator)
        .join(Indicator, ReportIndicator.indicator_id == Indicator.id)
        .filter(ReportIndicator.report_id == report.id)
        .all()
    )
    indicators = [
        SavedIndicatorAnalysis(
            indicator_id=ind.id,
            indicator_name=ind.name,
            analysis=ri.analysis,
            suggestion=ri.suggestion,
            is_positive=ri.is_positive,
        )
        for ri, ind in rows
    ]
    return ReportGetResponse(
        report_id=report.id,
        student_id=student_id,
        exam_id=exam_id,
        indicators=indicators,
    )
