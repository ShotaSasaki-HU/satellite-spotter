# app/routers/locations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import location as crud_location
from app.db import session
from app.schemas import location as schemas_location

router = APIRouter()
@router.get("/api/v1/locations", response_model=list[schemas_location.Location])
def search_locations(q: str, lat: float, lon: float, db: Session = Depends(session.get_db)):
    results = crud_location.search_locations_and_sort_by_distance(
        db=db, name=q, lat=lat, lon=lon
    )
    return results
