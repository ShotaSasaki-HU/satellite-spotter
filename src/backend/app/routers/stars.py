# app/routers/stars.py
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, timezone
from app.schemas.star import StarResponse, StarPosition
from app.services.astro_service import AstroDataService, get_astro_data_service
from app.services.star_service import get_visible_stars

router = APIRouter()
@router.get("/api/v1/stars", response_model=StarResponse)
def get_starry_sky_snapshot(
        time: datetime = Query(...),
        lat: float = Query(...),
        lon: float = Query(...),
        astro_service: AstroDataService = Depends(get_astro_data_service)):
    """
    指定された時刻における，観測可能な恒星の方位角・仰角を返す．
    """
    try:
        # UTCとしてタイムゾーンを保証
        if time.tzinfo is None:
            time_utc = time.replace(tzinfo=timezone.utc)
        else:
            time_utc = time.astimezone(timezone.utc)

        # サービスレイヤーを呼び出して星の位置を一括計算
        raw_stars = get_visible_stars(lat=lat, lon=lon, time_utc=time_utc, astro_service=astro_service)
        
        # Pydanticモデルにマッピング
        positions = [StarPosition(**star_data) for star_data in raw_stars]

        return StarResponse(
            timestamp=time_utc.isoformat(),
            positions=positions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"星空データの計算中にエラーが発生しました: {str(e)}")
