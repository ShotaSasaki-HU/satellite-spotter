# app/routers/stars.py
from fastapi import APIRouter, Query, Depends
from app.schemas import star as schemas_star
from datetime import datetime
from app.services.sat_service import SatDataService, get_sat_data_service
from skyfield.api import Topos, load, Star
from skyfield.data import hipparcos

router = APIRouter()
@router.get("/api/v1/stars", response_model=schemas_star.StarResponse)
def get_starry_sky_snapshot(
        time: datetime = Query(...),
        lat: float = Query(...),
        lon: float = Query(...),
        sat_service: SatDataService = Depends(get_sat_data_service)):
    """
    指定された時刻における，恒星の方位角・仰角を返す．
    """
    ts = sat_service.get_timescale()
    t_target = ts.from_datetime(time)

    return
