# app/crud/location.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, union_all, func
from app.models import Location, Spot
from geoalchemy2.functions import ST_Distance
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

    queries = []
    # 検索対象のモデルをリスト化
    for model in [Location, Spot]:
        conditions = [model.name.contains(kw) for kw in keywords]
        query = (
            db.query(
                model.name.label('name'),
                cast(model.geom, Geometry).ST_Y().label('lat'),
                cast(model.geom, Geometry).ST_X().label('lon'),
                model.geom.label('geom')
            )
            .filter(and_(*conditions))
        )
        queries.append(query)

    # 2つのクエリを統合してサブクエリとして扱う．
    # .subqueryでラップすることで，'unified_sq' という名前の仮想テーブルになる．
    unified_sq = union_all(*queries).subquery("unified_sq")

    # ページネーション前の総件数をサブクエリから取得
    total_query = db.query(func.count()).select_from(unified_sq)
    total = total_query.scalar()

    center_point = f"SRID=4326;POINT({lon} {lat})" # lon -> latの順に注意！

    # 距離でソート・ページネーションを適用
    results = (
        db.query(unified_sq)
        .order_by(
            ST_Distance(
                unified_sq.c.geom, # 仮想テーブルのカラムは .c 経由でアクセス
                center_point
            )
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return total, results
