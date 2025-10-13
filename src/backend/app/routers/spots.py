# app/routers/spots.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import spot as crud_spot
from app.db import session
from app.schemas import spot as schemas_spot

router = APIRouter()
@router.get("/api/v1/spots", response_model=schemas_spot.SpotsResponse)
def search_spots(
        lat: float,
        lon: float,
        radius: int,
        db: Session = Depends(session.get_db)
    ):
    """
    指定された中心座標から半径radius(km)以内にある観測スポットの候を検索する。
    """
    spots_list = crud_spot.get_spots_within_radius(
        db=db, lat=lat, lon=lon, radius_km=radius
    )

    # スキーマの形に合わせて，totalとspotsを含む辞書を返す．
    return {"total": len(spots_list), "spots": spots_list}
