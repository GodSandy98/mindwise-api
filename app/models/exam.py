from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
