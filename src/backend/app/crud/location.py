# app/crud/location.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app import models
import math

def search_locations_and_sort_by_distance(
        db: Session,
        name: str,
        lat: float,
        lon: float,
        skip: int = 0,
        limit: int = 20
    ):
    """
    スペース区切りの全ての検索クエリを名前に含むLocationをAND検索し，
    指定された座標に近い順にソートしてリストを返す．
    """
    keywords = name.split()
    if not keywords:
        return []
    
    # 各キーワードに対する.contains()条件をリストとして作成
    conditions = [models.Location.name.contains(kw) for kw in keywords]

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    db_lat_rad = func.radians(models.Location.lat)
    db_lon_rad = func.radians(models.Location.lon)

    # 球面三角法による距離計算（単位：km）
    # 6371 は地球の半径
    distance_formula = 6371 * func.acos(
        (func.sin(lat_rad) * func.sin(db_lat_rad)) +
        (func.cos(lat_rad) * func.cos(db_lat_rad) * func.cos(db_lon_rad - lon_rad))
    )

    query = (
        db.query(models.Location)
        .filter(and_(*conditions)) # and_() を使って全てのキーワードによる条件を結合
        .order_by(distance_formula) # 距離でソート
    )

    return query.offset(skip).limit(limit).all()
