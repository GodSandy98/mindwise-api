from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # super_admin | admin_teacher | class_teacher
    class_id = Column(Integer, ForeignKey("class.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
