from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClassResponse(BaseModel):
    id: int
    name: str
    is_active: bool = True
    graduated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClassWithStudentsResponse(BaseModel):
    id: int
    name: str
    students: list[dict]

    class Config:
        from_attributes = True


class ClassRenameRequest(BaseModel):
    name: str


class ClassBatchPromoteRequest(BaseModel):
    class_ids: list[int]
    find: str        # 要替换的文字，如 "高一"
    replace: str     # 替换为，如 "高二"
