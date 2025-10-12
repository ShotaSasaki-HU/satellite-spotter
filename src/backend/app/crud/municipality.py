# app/crud/municipality.py
from sqlalchemy.orm import Session
from app import models

def get_municipalities_by_name(db: Session, name: str, skip: int = 0, limit: int = 100):
    return db.query(models.Municipality).filter(models.Municipality.name.contains(name)).offset(skip).limit(limit).all()
