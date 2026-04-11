from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


# ── Generate ─────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    student_id: int = Field(..., description="学生ID")
    exam_id: int = Field(..., description="考试ID")


class IndicatorAnalysis(BaseModel):
    indicator_id: int
    indicator_name: str
    score_raw: float
    score_standardized: float
    level: str  # H / M / L
    system: str  # motivation / regulation / execution
    analysis: str  # LLM-generated, student-facing
    analysis_teacher: str = ""  # LLM-generated, teacher-facing
    suggestion: Optional[str] = None  # only for bottom 3


class SystemLevelResult(BaseModel):
    system: str
    avg_z: float
    level: str


class PersonaResult(BaseModel):
    code: str
    teacher_label: str
    teacher_description: str
    student_label: str
    student_description: str


class ReportGenerateResponse(BaseModel):
    student_id: int
    exam_id: int
    persona: PersonaResult
    system_levels: List[SystemLevelResult]
    summary: str = ""                        # LLM综合概述，学生口吻
    strengths: List[IndicatorAnalysis]       # top 3
    weaknesses: List[IndicatorAnalysis]      # bottom 3 (with suggestions)


# ── Save ─────────────────────────────────────────────────────

class ReportSaveRequest(BaseModel):
    student_id: int
    exam_id: int
    persona_code: str
    motivation_level: str
    regulation_level: str
    execution_level: str
    summary: str = ""
    strengths: List[IndicatorAnalysis]
    weaknesses: List[IndicatorAnalysis]


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


# ── Get ──────────────────────────────────────────────────────

class ReportGetResponse(BaseModel):
    report_id: int
    student_id: int
    exam_id: int
    persona: Optional[PersonaResult] = None
    motivation_level: Optional[str] = None
    regulation_level: Optional[str] = None
    execution_level: Optional[str] = None
    summary: Optional[str] = None
    indicators: List[SavedIndicatorAnalysis]


# ── History ──────────────────────────────────────────────────

class IndicatorVersion(BaseModel):
    version: int
    analysis: Optional[str] = None
    suggestion: Optional[str] = None
    is_current: bool
    created_at: datetime


class IndicatorHistory(BaseModel):
    indicator_id: int
    indicator_name: str
    is_positive: bool
    versions: List[IndicatorVersion]


class IndicatorHistoryResponse(BaseModel):
    report_id: int
    student_id: int
    exam_id: int
    indicators: List[IndicatorHistory]


# ── Batch ────────────────────────────────────────────────────

class BatchGenerateRequest(BaseModel):
    exam_id: int = Field(..., description="考试ID")
    class_id: Optional[int] = Field(None, description="班级ID（可选，不传则全校）")
    student_ids: Optional[List[int]] = Field(None, description="指定学生ID列表（可选，不传则按class_id/全校）")


class StudentReportStatus(BaseModel):
    student_id: int
    student_name: str
    class_id: int
    class_name: str
    has_report: bool
