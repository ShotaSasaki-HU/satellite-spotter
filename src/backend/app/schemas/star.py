# app/schemas/star.py
from pydantic import BaseModel

class StarPosition(BaseModel):
    star_name: str
    az: float
    alt: float
    magnitude: float # 等級

class StarResponse(BaseModel):
    timestamp: str
    positions: list[StarPosition]
