# app/schemas/location.py
from pydantic import BaseModel

class Location(BaseModel):
    name: str
    lat: float
    lon: float

    class Config:
        from_attributes = True # SQLAlchemyモデル（app/models/location.py）から自動でこのデータ構造に変換できるようにする設定

# APIレスポンス全体を表すスキーマ
class LocationsResponse(BaseModel):
    total: int
    locations: list[Location]
