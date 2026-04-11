from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.core.database import Base


class IndicatorText(Base):
    """Pre-written analysis/suggestion templates for each leaf indicator at each level."""
    __tablename__ = "indicator_texts"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    level = Column(String(1), nullable=False)  # H / M / L
    view = Column(String(10), nullable=False)  # "teacher" / "student"

    analysis = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    golden_quote = Column(Text, nullable=True)  # optional motivational quote
