# app/models/location.py
from sqlalchemy import Column, Integer, String
from app.db.base_class import Base
from geoalchemy2 import Geography

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    geom = Column(Geography(geometry_type='POINT', srid=4326), nullable=False) # SRID=4326：世界測地系（WGS84）
