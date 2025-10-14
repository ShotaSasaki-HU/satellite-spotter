# app/routers/recommendations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import session
from app.schemas import event as schemas_event
from app.crud import spot as crud_spot
from app.services.event_service import get_events_for_the_coord

router = APIRouter()
@router.get("/api/v1/recommendations/events", response_model=schemas_event.EventResponse)
def recommend_events(
    lat: float,
    lon: float,
    radius: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(session.get_db)
):
    # 1. 探索中心と探索半径を用いて，観測候補スポットのRowオブジェクトのリストを取得．
    potential_spots = crud_spot.get_top_spots_by_static_score(
        db=db, lat=lat, lon=lon, radius_km=radius, limit=10
    )

    # 2. スポットそれぞれについて観測イベントのリストを取得して統合
    unified_events = []
    for row in potential_spots:
        events_for_the_spot = get_events_for_the_coord(
            lat=row.geom.ST_Y(),
            lon=row.geom.ST_X(),
            horizon_profile=row.horizon_profile,
            sky_glow_score=row.sky_glow_score
        )
        if events_for_the_spot:
            unified_events.extend(events_for_the_spot)

    # 3. visibilityが高い順にソート
    top_events = sorted(unified_events, key=lambda e: e.visibility, reverse=True)
    total = len(top_events)
    
    return {'total': total, 'events': top_events[offset:offset+limit]}
