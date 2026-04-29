from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    scores_computed_at = Column(DateTime, nullable=True)  # set whenever scores are (re)computed
