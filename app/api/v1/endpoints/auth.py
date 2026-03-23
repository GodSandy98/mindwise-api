from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.teacher import Teacher
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, TeacherRegister, TeacherResponse
from app.api.v1.deps import get_current_teacher

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.phone == payload.phone).first()
    if not teacher or not verify_password(payload.password, teacher.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误")
    if not teacher.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    token = create_access_token({"sub": teacher.phone, "role": teacher.role, "class_id": teacher.class_id})
    return TokenResponse(access_token=token)


@router.post("/register", response_model=TeacherResponse, status_code=201)
def register(payload: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")
    teacher = Teacher(
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        role="class_teacher",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/me", response_model=TeacherResponse)
def get_me(current: Teacher = Depends(get_current_teacher)):
    return current
