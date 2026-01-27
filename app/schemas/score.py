# app/schemas/score.py
from pydantic import BaseModel, Field
from typing import List, Optional


class ScoreComputeRequest(BaseModel):
    exam_id: int = Field(..., description="Which exam the question belongs to")


class IndicatorScore(BaseModel):
    indicator_id: int
    score_raw: float
    score_standardized: Optional[float] = None


class StudentScoreResult(BaseModel):
    student_id: int
    exam_id: int
    indicator_scores: List[IndicatorScore] = Field(default_factory=list)


class ScoreComputeResponse(BaseModel):
    results: List[StudentScoreResult] = Field(default_factory=list)
