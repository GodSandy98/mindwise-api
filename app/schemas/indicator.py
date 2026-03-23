from pydantic import BaseModel
from typing import Optional


class IndicatorResponse(BaseModel):
    id: int
    name: str
    system: Optional[str] = None

    class Config:
        from_attributes = True
