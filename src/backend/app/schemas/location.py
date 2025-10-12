# app/schemas/location.py
from pydantic import BaseModel

class Location(BaseModel):
    name: str
    lat: float
    lon: float

    class Config:
        orm_mode = True # SQLAlchemyモデル（app/models/location.py）から自動でこのデータ構造に変換できるようにする設定
