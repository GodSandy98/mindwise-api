from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.answer import Answer
from app.models.student import Student
from app.models.exam import Exam
from app.models.question import Question
from app.models.teacher import Teacher
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse
from app.api.v1.deps import get_current_teacher, assert_student_class_access

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("/submit", response_model=AnswerSubmitResponse)
def submit_answers(payload: AnswerSubmitRequest, db: Session = Depends(get_db), current: Teacher = Depends(get_current_teacher)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"student_id={payload.student_id} 不存在")
    assert_student_class_access(current, student.class_id)
    if not db.query(Exam).filter(Exam.id == payload.exam_id).first():
        raise HTTPException(status_code=404, detail=f"exam_id={payload.exam_id} 不存在")
    question_ids = [a.question_id for a in payload.answers]
    existing_questions = {q.id for q in db.query(Question).filter(Question.id.in_(question_ids)).all()}
    missing = [qid for qid in question_ids if qid not in existing_questions]
    if missing:
        raise HTTPException(status_code=404, detail={"message": "题目不存在", "missing_question_ids": missing})
    try:
        with db.begin_nested():
            db.query(Answer).filter(Answer.student_id == payload.student_id, Answer.exam_id == payload.exam_id).delete(synchronize_session=False)
            db.add_all([Answer(student_id=payload.student_id, exam_id=payload.exam_id, question_id=item.question_id, answer=item.answer) for item in payload.answers])
        return AnswerSubmitResponse(student_id=payload.student_id, exam_id=payload.exam_id, count=len(payload.answers))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": "提交答案失败", "error": str(e)})
