# app/schemas/score.py
from pydantic import BaseModel, Field
from typing import List, Optional


class ScoreComputeRequest(BaseModel):
    student_ids: List[int] = Field(..., description="Target student IDs")
    release: int = Field(..., description="Test release / round number")


class IndicatorScore(BaseModel):
    indicator_id: int
    score_raw: float
    score_standardized: Optional[float] = None


class StudentScoreResult(BaseModel):
    student_id: int
    release: int
    indicator_scores: List[IndicatorScore] = Field(default_factory=list)


class ScoreComputeResponse(BaseModel):
    results: List[StudentScoreResult] = Field(default_factory=list)
