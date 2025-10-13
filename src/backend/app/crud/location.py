# app/crud/location.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Location
from geoalchemy2.functions import ST_Distance
from sqlalchemy import cast
from geoalchemy2.types import Geometry

def search_locations_and_sort_by_distance(
        db: Session,
        name: str,
        lat: float,
        lon: float,
        limit: int = 10,
        offset: int = 0
    ):
    """
    スペース区切りの全ての検索クエリを名前に含むLocationをAND検索し，
    指定された座標に近い順にソートしてリストを返す．
    """
    keywords = name.split()
    if not keywords:
        return 0, []
    
    # 各キーワードに対する.contains()条件をリストとして作成
    conditions = [Location.name.contains(kw) for kw in keywords]

    # 検索中心（SRID=4326：世界測地系WGS84）
    center_point = f"SRID=4326;POINT({lon} {lat})" # lon -> latの順に注意！

    base_query = (
        db.query(
            Location,
            cast(Location.geom, Geometry).ST_Y().label('lat'),
            cast(Location.geom, Geometry).ST_X().label('lon')
        )
        .filter(and_(*conditions)) # and_() を使って全てのキーワードによる条件を結合
    )

    # ページネーションを適用する前に総件数を取得
    total = base_query.count()

    # 距離でソート・ページネーションを適用
    results = (
        base_query
        .order_by(
            ST_Distance(
                Location.geom,
                center_point
            )
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, results
