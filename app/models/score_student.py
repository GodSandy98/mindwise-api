from sqlalchemy import Column, Integer, Float, ForeignKey
from app.core.database import Base


class ScoreStudent(Base):
    __tablename__ = "score_student"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    score_raw = Column(Float, nullable=False)
    score_standardized = Column(Float, nullable=False)
    release = Column(Integer, nullable=False)
