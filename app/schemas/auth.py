from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TeacherCreate(BaseModel):
    phone: str
    password: str
    name: str
    role: str  # admin_teacher | class_teacher (super_admin creates these)
    class_id: Optional[int] = None


class TeacherRegister(BaseModel):
    phone: str
    password: str
    name: str


class TeacherUpdate(BaseModel):
    role: Optional[str] = None
    class_id: Optional[int] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    phone: str
    name: str
    role: str
    class_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True
