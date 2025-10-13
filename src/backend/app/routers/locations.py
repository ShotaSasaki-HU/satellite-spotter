# app/routers/locations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import location as crud_location
from app.db import session
from app.schemas import location as schemas_location

router = APIRouter()
@router.get("/api/v1/locations", response_model=schemas_location.LocationsResponse)
def search_locations(
        q: str,
        lat: float,
        lon: float,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(session.get_db)
    ):
    total, results_from_db = crud_location.search_locations_and_sort_by_distance(
        db=db, name=q, lat=lat, lon=lon, limit=limit, offset=offset
    )

    locations_for_response = []
    for row in results_from_db:
        locations_for_response.append(
            schemas_location.Location(
                name=row.name,
                lat=row.lat,
                lon=row.lon
            )
        )

    return {"total": total, "locations": locations_for_response}
