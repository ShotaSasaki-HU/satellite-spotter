# app/schemas/municipality.py
from pydantic import BaseModel

class Municipality(BaseModel):
    name: str
    lat: float
    lon: float

    class Config:
        orm_mode = True # SQLAlchemyモデルから自動で変換できるようにする設定
