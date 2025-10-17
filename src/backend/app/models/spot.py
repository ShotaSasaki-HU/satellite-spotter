# app/models/spot.py
from sqlalchemy import Column, Integer, String, ARRAY, Float, BigInteger
from app.db.base_class import Base
from geoalchemy2 import Geography

class Spot(Base):
    __tablename__ = "spots"

    id = Column(Integer, primary_key=True, index=True) # アプリ専用の主id
    osm_id = Column(BigInteger, unique=True, index=True, nullable=True) # OSMのID

    name = Column(String, nullable=False)
    name_en = Column(String, nullable=True)

    # 座標をGeography型で一元管理．SRID=4326は世界測地系(WGS84)を示す値．
    geom = Column(Geography(geometry_type='POINT', srid=4326), nullable=False) # 代表座標
    polygon_geom = Column(Geography(geometry_type='POLYGON', srid=4326), nullable=True) # POLYGONがあれば格納

    # 時間的に変化しない静的な評価指標
    horizon_profile = Column(ARRAY(Float), nullable=True)
    sqm_value = Column(Float, nullable=True)

    elevation_m = Column(Float, nullable=True) # 標高（m）
