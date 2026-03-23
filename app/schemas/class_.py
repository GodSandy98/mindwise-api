from pydantic import BaseModel
from typing import List


class ClassResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ClassWithStudentsResponse(BaseModel):
    id: int
    name: str
    students: List[dict]

    class Config:
        from_attributes = True
