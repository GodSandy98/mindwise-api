from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)  # TEXT 类型
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    num_choices = Column(Integer, nullable=False)  # 实际是 TINYINT，SQLAlchemy 用 Integer
    is_negative = Column("is_negative", Boolean, nullable=False, default=False)