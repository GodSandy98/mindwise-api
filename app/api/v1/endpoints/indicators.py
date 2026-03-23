from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.indicator import Indicator
from app.models.teacher import Teacher
from app.schemas.indicator import IndicatorResponse
from app.api.v1.deps import get_current_teacher

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("", response_model=List[IndicatorResponse])
def get_all_indicators(db: Session = Depends(get_db), _: Teacher = Depends(get_current_teacher)):
    return db.query(Indicator).all()
