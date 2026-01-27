from sqlalchemy import Column, Integer, Text, Boolean
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    num_choices = Column(Integer, nullable=False)
    is_negative = Column(Boolean, nullable=False, default=False)
