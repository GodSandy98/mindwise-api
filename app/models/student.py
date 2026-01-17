from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    class_id = Column(Integer, ForeignKey("class.id"), nullable=False)
