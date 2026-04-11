from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    system = Column(String(50))          # "motivation" / "regulation" / "execution"
    parent_id = Column(Integer, ForeignKey("indicators.id"), nullable=True)
    is_leaf = Column(Integer, nullable=False, default=1)  # 1=leaf, 0=parent
