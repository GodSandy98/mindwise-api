from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class PersonaTemplate(Base):
    __tablename__ = "persona_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True)  # e.g. "HHH", "HHM", "HHL"
    motivation_level = Column(String(1), nullable=False)     # H / M / L
    regulation_level = Column(String(1), nullable=False)     # H / M / L
    execution_level = Column(String(1), nullable=False)      # H / M / L

    # Teacher version (diagnostic, direct)
    teacher_label = Column(String(100), nullable=False)
    teacher_description = Column(Text, nullable=False)

    # Student version (warm, empathetic)
    student_label = Column(String(100), nullable=False)
    student_description = Column(Text, nullable=False)
