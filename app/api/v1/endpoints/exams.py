from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.exam import Exam
from app.schemas.exam import ExamResponse

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=List[ExamResponse])
def get_all_exams(db: Session = Depends(get_db)):
    return db.query(Exam).order_by(Exam.date.desc()).all()


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail=f"exam_id={exam_id} 不存在")
    return exam
