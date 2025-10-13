# app/crud/spot.py
from sqlalchemy.orm import Session
from app.models import Spot
from geoalchemy2.functions import ST_DWithin
from sqlalchemy import cast
from geoalchemy2.types import Geometry

def search_spots_within_radius(
        db: Session,
        lat: float,
        lon: float,
        radius_km: int,
        limit: int = 10,
        offset: int = 0
    ):
    """
    指定された中心座標から半径内にあるスポットを検索し，総件数とページネーション適用後の結果を返す．
    DBからAPIサーバーへ無駄なデータを流さないために，CRUD関数がページネーションを担う．
    """
    # 検索中心（SRID=4326：世界測地系WGS84）
    center_point = f"SRID=4326;POINT({lon} {lat})" # lon -> latの順に注意！

    radius_m = radius_km * 1000

    base_query = (
        db.query(
            Spot,
            cast(Spot.geom, Geometry).ST_Y().label('lat'),
            cast(Spot.geom, Geometry).ST_X().label('lon')
        )
        .filter(
            ST_DWithin(
                Spot.geom,    # スポットのgeomカラム
                center_point, # 検索中心のポイント
                radius_m      # 検索半径（m）
            )
        )
    )

    # ページネーションを適用する前に総件数を取得
    total = base_query.count()

    # ページネーションを適用
    results = base_query.offset(offset).limit(limit).all()

    return total, results
