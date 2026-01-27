from sqlalchemy import Column, Integer, ForeignKey

from app.core.database import Base


class IndicatorQuestion(Base):
    __tablename__ = "indicator_question"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
