from pydantic import BaseModel, Field
from typing import List, Optional


class ReportGenerateRequest(BaseModel):
    student_id: int = Field(..., description="学生ID")
    exam_id: int = Field(..., description="考试ID")


class IndicatorAnalysis(BaseModel):
    indicator_name: str
    score_standardized: float
    level: str  # H / M / L
    analysis: str


class ImprovementSuggestion(BaseModel):
    indicator_name: str
    suggestion: str


class ReportGenerateResponse(BaseModel):
    student_id: int
    exam_id: int
    strengths_analysis: List[IndicatorAnalysis] = Field(
        description="三、具体指标优势项分析（得分最高的三项）"
    )
    weaknesses_analysis: List[IndicatorAnalysis] = Field(
        description="四、具体指标不足分析（得分最低的三项）"
    )
    improvement_suggestions: List[ImprovementSuggestion] = Field(
        description="五、针对性改进建议（针对最低三项各一条）"
    )


class ReportSaveRequest(BaseModel):
    student_id: int
    exam_id: int
    strengths_analysis: List[IndicatorAnalysis]
    weaknesses_analysis: List[IndicatorAnalysis]
    improvement_suggestions: List[ImprovementSuggestion]


class SavedIndicatorAnalysis(BaseModel):
    indicator_id: int
    indicator_name: str
    analysis: Optional[str] = None
    suggestion: Optional[str] = None
    is_positive: Optional[bool] = None


class ReportSaveResponse(BaseModel):
    report_id: int
    student_id: int
    exam_id: int
    indicators: List[SavedIndicatorAnalysis]


class ReportGetResponse(BaseModel):
    report_id: int
    student_id: int
    exam_id: int
    indicators: List[SavedIndicatorAnalysis]
