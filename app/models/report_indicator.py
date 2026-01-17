from sqlalchemy import Column, Integer, Text, ForeignKey, Boolean
from app.core.database import Base


class ReportIndicator(Base):
    __tablename__ = "report_indicator"

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    analysis = Column(Text)
    suggestion = Column(Text)
    is_positive = Column(Boolean, nullable=True)
