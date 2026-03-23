from pydantic import BaseModel, Field
from typing import List


class AnswerItem(BaseModel):
    question_id: int
    answer: int


class AnswerSubmitRequest(BaseModel):
    student_id: int
    exam_id: int
    answers: List[AnswerItem] = Field(..., min_length=1)


class AnswerSubmitResponse(BaseModel):
    student_id: int
    exam_id: int
    count: int
