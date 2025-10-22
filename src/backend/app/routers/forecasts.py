# app/routers/forecasts.py
from fastapi import APIRouter, Depends
from skyfield.api import load
import numpy as np
from app.schemas import event as schemas_event
from app.core.config import Settings, get_settings
from app.services.dem_service import get_elevations_by_coords, calc_horizon_profile_parallel
from app.services.event_service import get_events_for_the_coord, get_weather_dataframe_sync
from app.services.score_service import calc_sky_glow_score
from app.services.sat_service import SatDataService, get_sat_data_service

router = APIRouter()
@router.get("/api/v1/forecasts/events", response_model=schemas_event.EventResponse)
def forecast_events(
        lat: float,
        lon: float,
        limit: int = 10,
        offset: int = 0,
        settings: Settings = Depends(get_settings),
        sat_service: SatDataService = Depends(get_sat_data_service)):
    """
    スポットそれぞれについて観測イベントのリストを取得して統合する．
    """
    elevation_m = get_elevations_by_coords(coords=[{'lat': lat, 'lon': lon}],
                                           settings=settings)[0]
    if elevation_m < -1000 or np.isnan(elevation_m):
        print(f"⚠️ 警告: 観測地点 ({lat}, {lon}) の標高が取得できませんでした．")
        return {'total': 0, 'events': []}

    weather_df = get_weather_dataframe_sync(lat=lat, lon=lon, elevation_m=elevation_m)

    horizon_profile, azimuths = calc_horizon_profile_parallel(
        settings=settings,
        observer_lat=lat,
        observer_lon=lon,
        num_directions=180,
        max_distance=50000, # 事前計算より軽いパラメータ
        num_samples=50
    )
    horizon_profile = list(horizon_profile)

    sky_glow_score = calc_sky_glow_score(coords_to_sample=[(lon, lat)], settings=settings)[0]

    events = get_events_for_the_coord(
        location_name="",
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        horizon_profile=horizon_profile,
        sky_glow_score=sky_glow_score,
        sat_service=sat_service,
        weather_df=weather_df
    )

    # visibilityが高い順にソート
    events = sorted(events, key=lambda e: e.scores.visibility, reverse=True)
    total = len(events)
    
    return {'total': total, 'events': events[offset:offset+limit]}
