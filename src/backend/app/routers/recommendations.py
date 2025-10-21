# app/routers/recommendations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfield.api import load
import httpx
import asyncio
from app.db import session
from app.schemas import event as schemas_event
from app.crud import spot as crud_spot
from app.services.event_service import get_events_for_the_coord, fetch_weather_limited
from app.core.config import Settings, get_settings

router = APIRouter()
@router.get("/api/v1/recommendations/events", response_model=schemas_event.EventResponse)
async def recommend_events(
    lat: float,
    lon: float,
    radius: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(session.get_db),
    settings: Settings = Depends(get_settings)
):
    # 探索中心と探索半径を用いて，観測候補スポットのRowオブジェクトのリストを取得．
    potential_spots = crud_spot.get_top_spots_by_static_score(
        db=db, lat=lat, lon=lon, radius_km=radius, limit=10
    )

    # スポットそれぞれについて観測イベントのリストを取得して統合
    starlink_instances = load.tle(settings.PATH_TLE_STARLINK)
    station_instances = load.tle(settings.PATH_TLE_STATIONS)

    # 非同期HTTPクライアントを作成
    async with httpx.AsyncClient() as client:
        # 各スポットの天気予報を取得するタスクのリストを作成
        semaphore = asyncio.Semaphore(settings.OPEN_METEO_CONCURRENCY_LIMIT)
        weather_tasks = []
        for spot in potential_spots:
            task = asyncio.create_task(
                fetch_weather_limited(
                    lat=spot.lat,
                    lon=spot.lon,
                    elevation_m=spot.elevation_m,
                    client=client,
                    semaphore=semaphore
                )
            )
            weather_tasks.append(task)
        
        # asyncio.gatherでタスクを並行処理（セマフォにより同時実行数が制限されている．）
        weather_forecasts = await asyncio.gather(*weather_tasks)

    unified_events = []
    for row, weather_df in zip(potential_spots, weather_forecasts):
        events_for_the_spot = get_events_for_the_coord(
            location_name=row.name,
            lat=row.lat,
            lon=row.lon,
            elevation_m=row.elevation_m,
            horizon_profile=row.horizon_profile,
            sky_glow_score=row.sky_glow_score,
            starlink_instances=starlink_instances,
            station_instances=station_instances,
            weather_df=weather_df
        )
        if events_for_the_spot:
            unified_events.extend(events_for_the_spot)

    # visibilityが高い順にソート
    top_events = sorted(unified_events, key=lambda e: e.visibility, reverse=True)
    total = len(top_events)
    
    return {'total': total, 'events': top_events[offset:offset+limit]}
