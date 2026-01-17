from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.student import Student
from app.models.class_ import Class
from app.schemas.student import StudentResponse

router = APIRouter()


# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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