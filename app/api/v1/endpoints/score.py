import math
from typing import List, Dict, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.students import _fetch_students_or_404, _validate_and_dedup_student_ids
from app.db.session import get_db
from app.db.sql_loader import load_text_query
from app.schemas.score import (
    ScoreComputeRequest,
    ScoreComputeResponse,
    StudentScoreResult,
    IndicatorScore,
)

from app.models.student import Student
from app.models.score_student import ScoreStudent

router = APIRouter(prefix="/scores", tags=["scores"])


@router.post("/compute", response_model=ScoreComputeResponse)
def compute_score_api(
    payload: ScoreComputeRequest,
    db: Session = Depends(get_db)
) -> ScoreComputeResponse:
    """
    根据student_id和release，计算student的score
    逻辑是先把这次release的均分计算，再根据这次release下面student的answer激素那score
    :param payload:
    :param db:
    :return:
    """
    try:
        student_ids = _validate_and_dedup_student_ids(payload.student_ids)
        students_by_id = _fetch_students_or_404(db, student_ids)

        raw_scores = _compute_score_raw_avg(db, student_ids, payload.release)
        stats_by_indicator = _compute_indicator_stats_for_release(db, payload.release)

        scores = _apply_standardization(raw_scores, stats_by_indicator)

        with db.begin_nested():
            _upsert_scores(db, student_ids, payload.release, scores)
            return _build_response(student_ids, payload.release, students_by_id, scores)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()   # 安全兜底（with begin 已经 rollback 过，这里不会有副作用）
        raise HTTPException(status_code=500, detail={"message": "internal server error", "error": str(e)})


def _compute_score_raw_avg(
    db: Session,
    student_ids: List[int],
    release: int,
) -> Dict[int, List[dict]]:
    out: Dict[int, List[dict]] = {sid: [] for sid in student_ids}

    stmt = load_text_query("score_raw_avg", expanding_params=("student_ids",))
    rows = db.execute(stmt, {"release": release, "student_ids": student_ids}).mappings().all()

    for r in rows:
        sid = int(r["student_id"])
        out[sid].append(
            {
                "indicator_id": int(r["indicator_id"]),
                "score_raw": float(r["score_raw"]) if r["score_raw"] is not None else 0.0,
            }
        )
    return out


def _compute_indicator_stats_for_release(db: Session, release: int) -> Dict[int, Tuple[float, float]]:
    """
    返回：{indicator_id: (mean, std)}
    - mean/std 均基于“全校该 release”的 raw（按学生-指标先 AVG 得到 raw，再在指标维度统计）
    - std 由 variance 开方得到；variance<=0 视为 std=0
    """
    stmt = load_text_query("indicator_stats_release")  # 对应 app/sql/indicator_stats_release.sql

    rows = db.execute(stmt, {"release": release}).mappings().all()

    stats: Dict[int, Tuple[float, float]] = {}
    for r in rows:
        indicator_id = int(r["indicator_id"])
        mean = float(r["mean"]) if r["mean"] is not None else 0.0
        variance = float(r["variance"]) if r["variance"] is not None else 0.0

        if variance <= 0:
            std = 0.0
        else:
            std = math.sqrt(variance)

        stats[indicator_id] = (mean, std)
    return stats


def _apply_standardization(
    raw_scores: Dict[int, List[dict]],
    stats_by_indicator: Dict[int, Tuple[float, float]],
) -> Dict[int, List[dict]]:
    """
    根据raw_score和stats_by_indicator计算score_standardized
    :param raw_scores: {student_id: [{"indicator_id": int, "score_raw": float}, ...]}
    :param stats_by_indicator: stats_by_indicator: {indicator_id: (mean, std)}
    :return: scores: {student_id: [{"indicator_id": int, "score_raw": float, "score_standardized": float|None}, ...]}
    """
    out: Dict[int, List[dict]] = {}

    for student_id, items in raw_scores.items():
        new_items: List[dict] = []

        for item in items:
            indicator_id = int(item["indicator_id"])
            score_raw = float(item["score_raw"])

            stats = stats_by_indicator.get(indicator_id)
            if not stats:
                score_std: Optional[float] = None
            else:
                mean, std = stats
                if std == 0:
                    score_std = 0
                else:
                    score_std = round((score_raw - mean) / std, 4)

            new_items.append(
                {
                    "indicator_id": indicator_id,
                    "score_raw": score_raw,
                    "score_standardized": score_std,
                }
            )

        out[student_id] = new_items

    return out


def _upsert_scores(
    db: Session,
    student_ids: list[int],
    release: int,
    scores_by_student: dict[int, list[dict]],
) -> None:
    """
    原子写入 score_student（raw + standardized）：
    - 幂等：同一批 student_ids + release 重算会覆盖旧数据
    - 原子：delete + insert 在同一个事务里，任一失败会整体回滚
    scores_by_student 的元素结构：
      { student_id: [ {"indicator_id": int, "score_raw": float, "score_standardized": float|None}, ... ] }
    """
    # 1) 删除旧数据
    db.query(ScoreStudent).filter(
        ScoreStudent.release == release,
        ScoreStudent.student_id.in_(student_ids),
    ).delete(synchronize_session=False)

    # 2) 批量插入新数据（raw + standardized 一起写）
    inserts: list[ScoreStudent] = []
    for sid in student_ids:
        for item in scores_by_student.get(sid, []):
            inserts.append(
                ScoreStudent(
                    student_id=sid,
                    indicator_id=int(item["indicator_id"]),
                    release=release,
                    score_raw=float(item["score_raw"]),
                    score_standardized=item.get("score_standardized"),
                )
            )

    if inserts:
        db.add_all(inserts)


def _build_response(
    student_ids: list[int],
    release: int,
    students_by_id: dict[int, "Student"],
    scores_by_student: dict[int, list[dict]],
) -> ScoreComputeResponse:
    results: list[StudentScoreResult] = []

    for sid in student_ids:
        items = scores_by_student.get(sid, [])
        indicator_scores = [
            IndicatorScore(
                indicator_id=int(x["indicator_id"]),
                score_raw=float(x["score_raw"]),
                score_standardized=x.get("score_standardized"),
            )
            for x in items
        ]

        results.append(
            StudentScoreResult(
                student_id=sid,
                release=release,
                indicator_scores=indicator_scores,
            )
        )

    return ScoreComputeResponse(results=results)
