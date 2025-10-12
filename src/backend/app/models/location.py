# app/models/location.py
from sqlalchemy import Column, Integer, String, Float
from app.db.base_class import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)
