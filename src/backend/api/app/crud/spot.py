# app/crud/spot.py
from sqlalchemy.orm import Session
from sqlalchemy import func, select, column, cast, Float, case
from app.models import Spot
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.types import Geometry
from app.core.config import Settings

def get_top_spots_by_static_score(
        db: Session,
        settings: Settings,
        lat: float,
        lon: float,
        radius_km: int,
        limit: int = 10) -> list:
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
    # B-1. World Atlas 2015の生値をSQM値に変換
    NATURAL_SKY_BRIGHTNESS_MCD_M2 = 0.171168465
    SQM_CONVERSION_CONSTANT = 108000000
    LOG_BASE_FACTOR = -0.4
    SQM_MIN = settings.SQM_MIN
    SQM_MAX = settings.SQM_MAX
    
    sqm_value_expr = func.coalesce( # Spot.wa2015_raw_valueがNULLの場合は，最悪値で計算．
        func.log10(
            (Spot.wa2015_raw_value + NATURAL_SKY_BRIGHTNESS_MCD_M2) / SQM_CONVERSION_CONSTANT
        ) / LOG_BASE_FACTOR,
        SQM_MIN
    )

    # B-2. SQM値を限界等級NELM（Naked-Eye Limiting Magnitude）に変換
    # 参考文献：Crumey, Andrew (2014). “Human Contrast Threshold and Astronomical Visibility”. Monthly Notices of the Royal Astronomical Society. 442 (3): 2600-2619.
    F = 2.0 # 典型的な観測者と仮定

    NELM_INTERCEPT_91 = -1.44 - (2.5 * func.log10(F))
    NELM_SLOPE_91 = 0.383

    NELM_INTERCEPT_90 = 0.8 - (2.5 * func.log10(F))
    NELM_SLOPE_90 = 0.27

    nelm_value_expr = case(
        (
            sqm_value_expr >= 19.5,
            (NELM_SLOPE_91 * sqm_value_expr) + NELM_INTERCEPT_91 # 参考文献の(91)式
        ),
        else_=(
            (NELM_SLOPE_90 * sqm_value_expr) + NELM_INTERCEPT_90 # 参考文献の(90)式
        )
    )

    # NELMをクリップ
    NELM_MIN = (NELM_SLOPE_90 * SQM_MIN) + NELM_INTERCEPT_90
    NELM_MAX = (NELM_SLOPE_91 * SQM_MAX) + NELM_INTERCEPT_91
    nelm_value_expr = func.least(func.greatest(nelm_value_expr, NELM_MIN), NELM_MAX)

    # NELMを0-1の範囲に正規化
    NELM_RANGE = NELM_MAX - NELM_MIN
    sky_glow_score_expr = case(
        (NELM_RANGE > 0, (nelm_value_expr - NELM_MIN) / NELM_RANGE),
        else_=0.0
    )

    # C. 最終的な静的スコアの計算式
    final_static_score = (topography_score_expr * sky_glow_score_expr)

    results_query = (
        db.query(
            Spot.name.label('name'),
            cast(Spot.geom, Geometry).ST_Y().label('lat'),
            cast(Spot.geom, Geometry).ST_X().label('lon'),
            Spot.elevation_m.label('elevation_m'),
            Spot.horizon_profile.label('horizon_profile'),
        )
        .filter(
            ST_DWithin(
                Spot.geom,    # スポットのgeomカラム
                center_point, # 検索中心のポイント
                radius_m      # 検索半径（m）
            )
        )
        .add_columns(sky_glow_score_expr.label('sky_glow_score'))
        .order_by(final_static_score.desc().nulls_last()) # デフォルトでは，NULLが先頭に来る．
        .limit(limit)
    )

    results = results_query.all() # Rowオブジェクトのlistになる．

    return results
