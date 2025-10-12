# app/schemas/municipality.py
from pydantic import BaseModel

class Municipality(BaseModel):
    name: str
    lat: float
    lon: float

    class Config:
        orm_mode = True # SQLAlchemyモデル（app/models/municipality.py）から自動でこのデータ構造に変換できるようにする設定
