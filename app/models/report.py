from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    release = Column(Integer, nullable=False)  # exam_id

    # Persona archetype
    persona_template_id = Column(Integer, ForeignKey("persona_templates.id"), nullable=True)
    persona = Column(String(255))  # cached label

    # System-level classifications (H/M/L)
    motivation_level = Column(String(1))
    regulation_level = Column(String(1))
    execution_level = Column(String(1))

    # LLM-generated comprehensive summary (student-facing)
    summary = Column(Text, nullable=True)
    