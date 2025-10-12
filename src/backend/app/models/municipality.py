# models/municipality.py
from sqlalchemy import Column, Integer, String, Float
from app.database import Base  # ここからBaseをimportする

class Municipality(Base):
    __tablename__ = "municipalities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)
