from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    system = Column(String(255))
