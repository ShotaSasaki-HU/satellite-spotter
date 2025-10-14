# app/crud/spot.py
from sqlalchemy.orm import Session
from app.models import Spot
from geoalchemy2.functions import ST_DWithin

def get_top_spots_by_static_score(
    db: Session,
    lat: float,
    lon: float,
    radius_km: int,
    limit: int = 10 # ページネーションではなく，足切り用．
) -> list[Spot]:
    """
    指定された中心座標から半径内にあるスポットを検索する．
    """
    # 検索中心（SRID=4326：世界測地系WGS84）
    center_point = f"SRID=4326;POINT({lon} {lat})" # lon -> latの順に注意！
    radius_m = radius_km * 1000

    # 足切りするため，適当に静的スコアを組み合わせて「場所の良さ」を概算．

    return (
        db.query(Spot)
        .filter(
            ST_DWithin(
                Spot.geom,    # スポットのgeomカラム
                center_point, # 検索中心のポイント
                radius_m      # 検索半径（m）
            )
        )
        .all() # Rowオブジェクトのlistになる．
    )
