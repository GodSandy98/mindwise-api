import math
from typing import List, Dict, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_teacher, class_filter, assert_student_class_access, require_admin_or_above
from app.db.session import get_db
from app.db.sql_loader import load_text_query
from app.models.student import Student
from app.models.score_student import ScoreStudent
from app.models.teacher import Teacher
from app.schemas.score import (
    ScoreComputeRequest,
    ScoreComputeResponse,
    StudentScoreResult,
    IndicatorScore,
)

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/student/{student_id}", response_model=StudentScoreResult)
def get_student_scores(student_id: int, exam_id: int, db: Session = Depends(get_db), current: Teacher = Depends(get_current_teacher)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"student_id={student_id} 不存在")
    assert_student_class_access(current, student.class_id)
    rows = db.query(ScoreStudent).filter(ScoreStudent.student_id == student_id, ScoreStudent.exam_id == exam_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"未找到得分，请先调用 /scores/compute")
    return StudentScoreResult(
        student_id=student_id,
        exam_id=exam_id,
        indicator_scores=[IndicatorScore(indicator_id=r.indicator_id, score_raw=r.score_raw, score_standardized=r.score_standardized) for r in rows],
    )


@router.get("/exam/{exam_id}", response_model=ScoreComputeResponse)
def get_exam_scores(exam_id: int, db: Session = Depends(get_db), current: Teacher = Depends(get_current_teacher)):
    query = db.query(ScoreStudent).filter(ScoreStudent.exam_id == exam_id)
    cid = class_filter(current)
    if cid is not None:
        student_ids = [s.id for s in db.query(Student).filter(Student.class_id == cid).all()]
        query = query.filter(ScoreStudent.student_id.in_(student_ids))
    rows = query.all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"未找到得分，请先调用 /scores/compute")
    by_student: Dict[int, List[dict]] = {}
    for r in rows:
        by_student.setdefault(r.student_id, []).append({"indicator_id": r.indicator_id, "score_raw": r.score_raw, "score_standardized": r.score_standardized})
    return _build_response(exam_id, by_student)


@router.post("/compute", response_model=ScoreComputeResponse)
def compute_score_api(payload: ScoreComputeRequest, db: Session = Depends(get_db), _: Teacher = Depends(require_admin_or_above)) -> ScoreComputeResponse:
    try:
        raw_scores = _compute_score_raw_avg(db, payload.exam_id)
        stats_by_indicator = _compute_indicator_stats_for_release(db, payload.exam_id)
        scores = _apply_standardization(raw_scores, stats_by_indicator)
        with db.begin_nested():
            _upsert_scores(db, payload.exam_id, scores)
            return _build_response(payload.exam_id, scores)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": "internal server error", "error": str(e)})


def _compute_score_raw_avg(db: Session, exam_id: int) -> Dict[int, List[dict]]:
    out: Dict[int, List[dict]] = {}
    stmt = load_text_query("score_raw_avg")
    rows = db.execute(stmt, {"exam_id": exam_id}).mappings().all()
    for row in rows:
        sid = int(row["student_id"])
        out.setdefault(sid, []).append({"indicator_id": int(row["indicator_id"]), "score_raw": float(row["score_raw"]) if row["score_raw"] is not None else 0.0})
    return out


def _compute_indicator_stats_for_release(db: Session, exam_id: int) -> Dict[int, Tuple[float, float]]:
    stmt = load_text_query("indicator_stats_release")
    rows = db.execute(stmt, {"exam_id": exam_id}).mappings().all()
    stats: Dict[int, Tuple[float, float]] = {}
    for row in rows:
        indicator_id = int(row["indicator_id"])
        mean = float(row["mean"]) if row["mean"] is not None else 0.0
        variance = float(row["variance"]) if row["variance"] is not None else 0.0
        stats[indicator_id] = (mean, 0.0 if variance <= 0 else math.sqrt(variance))
    return stats


def _apply_standardization(raw_scores: Dict[int, List[dict]], stats_by_indicator: Dict[int, Tuple[float, float]]) -> Dict[int, List[dict]]:
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
                score_std = 0 if std == 0 else round((score_raw - mean) / std, 4)
            new_items.append({"indicator_id": indicator_id, "score_raw": score_raw, "score_standardized": score_std})
        out[student_id] = new_items
    return out


def _upsert_scores(db: Session, exam_id: int, scores_by_student: dict[int, list[dict]]) -> None:
    db.query(ScoreStudent).filter(ScoreStudent.exam_id == exam_id).delete(synchronize_session=False)
    inserts: list[ScoreStudent] = []
    for sid, items in scores_by_student.items():
        for item in items:
            inserts.append(ScoreStudent(student_id=sid, indicator_id=int(item["indicator_id"]), exam_id=exam_id, score_raw=float(item["score_raw"]), score_standardized=item.get("score_standardized")))
    if inserts:
        db.add_all(inserts)


def _build_response(exam_id: int, scores_by_student: dict[int, list[dict]]) -> ScoreComputeResponse:
    results: list[StudentScoreResult] = []
    for sid, items in scores_by_student.items():
        results.append(StudentScoreResult(student_id=sid, exam_id=exam_id, indicator_scores=[IndicatorScore(indicator_id=int(x["indicator_id"]), score_raw=float(x["score_raw"]), score_standardized=x.get("score_standardized")) for x in items]))
    return ScoreComputeResponse(results=results)
