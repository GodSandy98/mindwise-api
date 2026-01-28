from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    persona = Column(String(255))
    motivational_system = Column(String(255))
    regulatory_system = Column(String(255))
    executive_system = Column(String(255))
    profile_interpretation = Column(Text)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    