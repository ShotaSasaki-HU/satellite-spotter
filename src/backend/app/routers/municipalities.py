# app/routers/municipalities.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import municipality as crud_municipality
from app.db import session
from app.schemas import municipality as schemas_municipality

router = APIRouter()
@router.get("/api/v1/municipalities/coordinates", response_model=list[schemas_municipality.Municipality])
def search_municipalities(q: str, db: Session = Depends(session.get_db)):
    results = crud_municipality.get_municipalities_by_name(db=db, name=q)
    return results
