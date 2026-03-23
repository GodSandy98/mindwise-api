from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.teacher import Teacher
from app.core.security import hash_password
from app.schemas.auth import TeacherCreate, TeacherUpdate, TeacherResponse
from app.api.v1.deps import require_super_admin

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=List[TeacherResponse])
def list_teachers(db: Session = Depends(get_db), _: Teacher = Depends(require_super_admin)):
    return db.query(Teacher).all()


@router.post("", response_model=TeacherResponse, status_code=201)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db), _: Teacher = Depends(require_super_admin)):
    if db.query(Teacher).filter(Teacher.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")
    teacher = Teacher(
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        class_id=payload.class_id,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.patch("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(teacher_id: int, payload: TeacherUpdate, db: Session = Depends(get_db), _: Teacher = Depends(require_super_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(teacher, field, value)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=204)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db), current: Teacher = Depends(require_super_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    if teacher.id == current.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    teacher.is_active = False
    db.commit()
