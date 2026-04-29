from pydantic import BaseModel
from typing import Optional


class IndicatorResponse(BaseModel):
    id: int
    name: str
    system: Optional[str] = None
    parent_id: Optional[int] = None
    is_leaf: int = 1

    class Config:
        from_attributes = True
