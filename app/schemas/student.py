from pydantic import BaseModel
from typing import Optional


class StudentResponse(BaseModel):
    id: int
    name: str
    class_id: int
    class_name: str

    class Config:
        from_attributes = True  # Pydantic v2 用法（替代 orm_mode）
