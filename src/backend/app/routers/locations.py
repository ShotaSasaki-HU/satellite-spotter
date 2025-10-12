# app/routers/locations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import location as crud_location
from app.db import session
from app.schemas import location as schemas_location

router = APIRouter()
@router.get("/api/v1/locations", response_model=list[schemas_location.Location])
def search_locations(q: str, db: Session = Depends(session.get_db)):
    results = crud_location.get_locations_by_name(db=db, name=q)
    return results
