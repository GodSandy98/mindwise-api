from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.student import Student
from app.models.class_ import Class
from app.schemas.student import StudentResponse

router = APIRouter()


def _fetch_students_or_404(db: Session, student_ids: list[int]) -> dict[int, Student]:
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    by_id = {s.id: s for s in students}
    missing = [sid for sid in student_ids if sid not in by_id]
    if missing:
        raise HTTPException(status_code=404, detail={"message": "students not found", "missing_student_ids": missing})
    return by_id


def _validate_and_dedup_student_ids(student_ids: list[int]) -> list[int]:
    if not student_ids:
        raise HTTPException(status_code=422, detail="student_ids cannot be empty")

    seen = set()
    unique_ids: list[int] = []
    for sid in student_ids:
        if not isinstance(sid, int) or sid <= 0:
            raise HTTPException(status_code=422, detail=f"invalid student_id: {sid}")
        if sid not in seen:
            seen.add(sid)
            unique_ids.append(sid)

    return unique_ids


@router.get("/students", response_model=list[StudentResponse])
def get_all_students(db: Session = Depends(get_db)):
    # 执行 JOIN 查询：students + class
    students = (
        db.query(Student, Class.name.label("class_name"))
        .join(Class, Student.class_id == Class.id)
        .all()
    )

    # 转换为 Pydantic 模型
    result = []
    for student, class_name in students:
        result.append(
            StudentResponse(
                id=student.id,
                name=student.name,
                class_id=student.class_id,
                class_name=class_name
            )
        )
    return result