# app/crud/location.py
from sqlalchemy.orm import Session
from app import models

def get_locations_by_name(db: Session, name: str, skip: int = 0, limit: int = 100):
    return db.query(models.Location).filter(models.Location.name.contains(name)).offset(skip).limit(limit).all()
