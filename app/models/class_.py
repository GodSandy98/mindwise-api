from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Class(Base):
    __tablename__ = "class"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
