from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("class.id"), nullable=True)  # None = all classes

    # Status: pending / running / done / failed
    status = Column(String(20), nullable=False, default="pending")

    total = Column(Integer, nullable=False, default=0)
    success = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)

    # JSON-encoded list of error dicts [{student_id, student_name, error}]
    errors = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
