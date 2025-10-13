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
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(session.get_db)
    ):
    """
    指定された中心座標から半径radius(km)以内にある観測スポットの候を検索する。
    """
    # CRUD関数は（Spotオブジェクト，緯度，経度）のタプルのリストを返す．
    total, results_from_db = crud_spot.search_spots_within_radius(
        db=db, lat=lat, lon=lon, radius_km=radius, limit=limit, offset=offset
    )

    # タプルのリストを、APIスキーマオブジェクトのリストに変換する
    spots_for_response = []
    for db_spot, spot_lat, spot_lon in results_from_db:
        spots_for_response.append(
            schemas_spot.Spot(
                id=db_spot.id,
                name=db_spot.name,
                lat=spot_lat,
                lon=spot_lon
            )
        )

    # スキーマの形に合わせて，totalとspotsを含む辞書を返す．
    return {"total": total, "spots": spots_for_response}
