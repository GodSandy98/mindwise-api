from pydantic import BaseModel
from datetime import datetime


class ExamResponse(BaseModel):
    id: int
    name: str
    date: datetime

    class Config:
        from_attributes = True
