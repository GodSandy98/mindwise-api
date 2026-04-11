from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.student import Student
from app.models.class_ import Class
from app.models.teacher import Teacher
from app.schemas.student import StudentResponse
from app.api.v1.deps import get_current_teacher, class_filter, assert_student_class_access

router = APIRouter(prefix="/students", tags=["students"])


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
def get_all_students(
    include_graduated: bool = Query(False),
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    query = db.query(Student, Class.name.label("class_name")).join(Class, Student.class_id == Class.id)
    cid = class_filter(current)
    if cid is not None:
        query = query.filter(Student.class_id == cid)
    elif not include_graduated:
        query = query.filter(Class.is_active == True)
    result = []
    for student, class_name in query.all():
        result.append(StudentResponse(id=student.id, name=student.name, class_id=student.class_id, class_name=class_name))
    return result


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    row = (
        db.query(Student, Class.name.label("class_name"))
        .join(Class, Student.class_id == Class.id)
        .filter(Student.id == student_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"student_id={student_id} 不存在")
    student, class_name = row
    assert_student_class_access(current, student.class_id)
    return StudentResponse(id=student.id, name=student.name, class_id=student.class_id, class_name=class_name)
