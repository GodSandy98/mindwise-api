from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.class_ import Class
from app.models.student import Student
from app.schemas.class_ import ClassResponse
from app.schemas.student import StudentResponse

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=List[ClassResponse])
def get_all_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()


@router.get("/{class_id}/students", response_model=List[StudentResponse])
def get_students_by_class(class_id: int, db: Session = Depends(get_db)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail=f"class_id={class_id} 不存在")

    rows = (
        db.query(Student, Class.name.label("class_name"))
        .join(Class, Student.class_id == Class.id)
        .filter(Student.class_id == class_id)
        .all()
    )
    return [
        StudentResponse(id=s.id, name=s.name, class_id=s.class_id, class_name=class_name)
        for s, class_name in rows
    ]
