from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.models.teacher import Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    payload = decode_token(token)
    phone: str = payload.get("sub")
    if not phone:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效 token")
    teacher = db.query(Teacher).filter(Teacher.phone == phone, Teacher.is_active == True).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return teacher


def require_super_admin(current: Teacher = Depends(get_current_teacher)) -> Teacher:
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return current


def require_admin_or_above(current: Teacher = Depends(get_current_teacher)) -> Teacher:
    if current.role not in ("super_admin", "admin_teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current


def require_psych_or_above(current: Teacher = Depends(get_current_teacher)) -> Teacher:
    """心理教师、管理教师、超级管理员可调用报告生成接口"""
    if current.role not in ("super_admin", "admin_teacher", "psych_teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要心理教师或以上权限")
    return current


def class_filter(teacher: Teacher) -> int | None:
    """Returns class_id to filter by, or None meaning no filter.
    Raises 403 if class_teacher has no assigned class yet."""
    if teacher.role == "class_teacher":
        if teacher.class_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="尚未分配班级，请联系管理员")
        return teacher.class_id
    return None


def assert_student_class_access(teacher: Teacher, student_class_id: int) -> None:
    if teacher.role == "class_teacher":
        if teacher.class_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="尚未分配班级，请联系管理员")
        if teacher.class_id != student_class_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该学生数据")


def assert_class_access(teacher: Teacher, class_id: int) -> None:
    if teacher.role == "class_teacher":
        if teacher.class_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="尚未分配班级，请联系管理员")
        if teacher.class_id != class_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该班级数据")
