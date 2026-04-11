from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_teacher, assert_class_access, class_filter, require_admin_or_above
from app.db.session import get_db
from app.models.class_ import Class
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.class_ import ClassResponse, ClassWithStudentsResponse, ClassRenameRequest, ClassBatchPromoteRequest
from app.schemas.student import StudentResponse

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=List[ClassResponse])
def get_all_classes(
    include_archived: bool = Query(False, description="是否包含已归档班级"),
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    query = db.query(Class)
    cid = class_filter(current)
    if cid is not None:
        query = query.filter(Class.id == cid)
    elif not include_archived:
        query = query.filter(Class.is_active == True)
    return query.order_by(Class.is_active.desc(), Class.name).all()


@router.get("/{class_id}/students", response_model=List[StudentResponse])
def get_students_by_class(
    class_id: int,
    db: Session = Depends(get_db),
    current: Teacher = Depends(get_current_teacher),
):
    assert_class_access(current, class_id)
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail=f"class_id={class_id} 不存在")
    rows = (
        db.query(Student, Class.name.label("class_name"))
        .join(Class, Student.class_id == Class.id)
        .filter(Student.class_id == class_id)
        .all()
    )
    return [StudentResponse(id=s.id, name=s.name, class_id=s.class_id, class_name=cn) for s, cn in rows]


@router.patch("/{class_id}", response_model=ClassResponse)
def rename_class(
    class_id: int,
    payload: ClassRenameRequest,
    db: Session = Depends(get_db),
    _: Teacher = Depends(require_admin_or_above),
):
    """重命名班级"""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    payload.name = payload.name.strip()
    if not payload.name:
        raise HTTPException(status_code=422, detail="班级名不能为空")
    if db.query(Class).filter(Class.name == payload.name, Class.id != class_id).first():
        raise HTTPException(status_code=409, detail=f"班级名「{payload.name}」已存在")
    cls.name = payload.name
    db.commit()
    db.refresh(cls)
    return cls


@router.post("/{class_id}/archive", response_model=ClassResponse)
def archive_class(
    class_id: int,
    db: Session = Depends(get_db),
    _: Teacher = Depends(require_admin_or_above),
):
    """归档班级（标记为已毕业，不删除数据）"""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    if not cls.is_active:
        raise HTTPException(status_code=409, detail="班级已经归档")
    cls.is_active = False
    cls.graduated_at = datetime.utcnow()
    db.commit()
    db.refresh(cls)
    return cls


@router.post("/{class_id}/restore", response_model=ClassResponse)
def restore_class(
    class_id: int,
    db: Session = Depends(get_db),
    _: Teacher = Depends(require_admin_or_above),
):
    """恢复归档班级"""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    if cls.is_active:
        raise HTTPException(status_code=409, detail="班级当前未归档")
    cls.is_active = True
    cls.graduated_at = None
    db.commit()
    db.refresh(cls)
    return cls


@router.post("/batch-promote", response_model=List[ClassResponse])
def batch_promote_classes(
    payload: ClassBatchPromoteRequest,
    db: Session = Depends(get_db),
    _: Teacher = Depends(require_admin_or_above),
):
    """批量升级：将所选班级名称中的指定文字替换（如「高一」→「高二」）"""
    if not payload.find.strip():
        raise HTTPException(status_code=422, detail="查找内容不能为空")
    if payload.find == payload.replace:
        raise HTTPException(status_code=422, detail="查找和替换内容相同，无需操作")

    classes = db.query(Class).filter(Class.id.in_(payload.class_ids), Class.is_active == True).all()
    if not classes:
        raise HTTPException(status_code=404, detail="未找到可升级的班级")

    updated = []
    for cls in classes:
        if payload.find not in cls.name:
            continue
        new_name = cls.name.replace(payload.find, payload.replace)
        if db.query(Class).filter(Class.name == new_name, Class.id != cls.id).first():
            raise HTTPException(status_code=409, detail=f"升级后的班级名「{new_name}」已存在，请先处理冲突")
        cls.name = new_name
        updated.append(cls)

    if not updated:
        raise HTTPException(status_code=422, detail=f"所选班级名称中均不含「{payload.find}」")

    db.commit()
    for cls in updated:
        db.refresh(cls)
    return updated
