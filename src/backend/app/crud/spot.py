# app/crud/spot.py
from sqlalchemy.orm import Session
from sqlalchemy import func, select, column, cast, Float, case
from app.models import Spot
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.types import Geometry

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
    # A. 簡易地形スコアの計算式（式オブジェクト）
    topography_score_expr = (
        select(func.count())
        .select_from(func.unnest(Spot.horizon_profile).alias('h'))
        .where(column('h') <= 3.0)
    ).scalar_subquery() / cast(func.cardinality(Spot.horizon_profile), Float)

    # B. 光害スコアの正規化式
    min_max_values = db.query(
        func.min(Spot.sky_glow_score),
        func.max(Spot.sky_glow_score)
    ).one()
    min_sg_score, max_sg_score = min_max_values
    # （最大 - 最小）が０になるケースを避けるため，caseで保護する．
    sky_glow_score_expr = case(
        (
            (max_sg_score - min_sg_score) > 0,
            1.0 - ((Spot.sky_glow_score - min_sg_score) / (max_sg_score - min_sg_score))
        ),
        else_=1.0 # 全て同じ値だった場合（太平洋上など）はスコア1とする．
    )

    # C. 最終的な静的スコアの計算式
    final_static_score = (topography_score_expr * sky_glow_score_expr).label("static_score")

    results_query = (
        db.query(
            Spot.name.label('name'),
            cast(Spot.geom, Geometry).ST_Y().label('lat'),
            cast(Spot.geom, Geometry).ST_X().label('lon'),
            Spot.horizon_profile.label('horizon_profile'),
            Spot.sky_glow_score.label('sky_glow_score')
        )
        .filter(
            ST_DWithin(
                Spot.geom,    # スポットのgeomカラム
                center_point, # 検索中心のポイント
                radius_m      # 検索半径（m）
            )
        )
        .add_columns(final_static_score)
        .order_by(final_static_score.desc())
        .limit(limit)
    )

    results = results_query.all() # Rowオブジェクトのlistになる．

    return results
