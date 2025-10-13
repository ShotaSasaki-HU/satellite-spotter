# app/schemas/spot.py
from pydantic import BaseModel

# リストの中の個々のスポットを表すスキーマ
class Spot(BaseModel):
    id: int # spot_idではない．
    name: str
    lat: float
    lon: float

    class Config:
        orm_mode = True

# APIレスポンス全体を表すスキーマ
class SpotsResponse(BaseModel):
    total: int
    spots: list[Spot] # Spotスキーマのリストとして定義
