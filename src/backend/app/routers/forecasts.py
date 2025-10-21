# app/routers/forecasts.py
from fastapi import APIRouter, Depends
from skyfield.api import load
import numpy as np
import rasterio
from app.schemas import event as schemas_event
from app.core.config import Settings, get_settings
from app.services.dem_service import get_elevations_by_coords, calc_horizon_profile_parallel
from app.services.event_service import get_events_for_the_coord, get_weather_dataframe_sync

router = APIRouter()
@router.get("/api/v1/forecasts/events", response_model=schemas_event.EventResponse)
def forecast_events(
        lat: float,
        lon: float,
        limit: int = 10,
        offset: int = 0,
        settings: Settings = Depends(get_settings)):
    # スポットそれぞれについて観測イベントのリストを取得して統合
    starlink_instances = load.tle(settings.PATH_TLE_STARLINK)
    station_instances = load.tle(settings.PATH_TLE_STATIONS)

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
        max_distance=100000,
        num_samples=100
    )
    horizon_profile = list(horizon_profile)

    # 光害スコアの計算と正規化
    # World Atlas 2015の生値をSQM値に変換
    with rasterio.open(settings.PATH_WORLD_ATLAS_2015_TIFF) as src:
        coord = [(lon, lat)]
        artificial_brightness = next(src.sample(coord))[0]
    if not artificial_brightness:
        print(f"⚠️ 警告: 観測地点 ({lat}, {lon}) に対応するWorld Atlas 2015の値が取得できませんでした．")
        return {'total': 0, 'events': []}

    NATURAL_SKY_BRIGHTNESS_MCD_M2 = 0.171168465
    SQM_CONVERSION_CONSTANT = 108000000
    LOG_BASE_FACTOR = -0.4
    SQM_MIN = 14.0 # 新宿で17.5程度
    SQM_MAX = 23.0

    total_brightness = artificial_brightness + NATURAL_SKY_BRIGHTNESS_MCD_M2
    sqm_value = np.log10(total_brightness / SQM_CONVERSION_CONSTANT) / LOG_BASE_FACTOR

    # SQM値を限界等級NELM（Naked-Eye Limiting Magnitude）に変換
    # 参考文献：Crumey, Andrew (2014). “Human Contrast Threshold and Astronomical Visibility”. Monthly Notices of the Royal Astronomical Society. 442 (3): 2600-2619.
    F = 2.0 # 典型的な観測者と仮定

    NELM_INTERCEPT_91 = -1.44 - (2.5 * np.log10(F))
    NELM_SLOPE_91 = 0.383

    NELM_INTERCEPT_90 = 0.8 - (2.5 * np.log10(F))
    NELM_SLOPE_90 = 0.27

    if sqm_value >= 19.5:
        nelm_value = (NELM_SLOPE_91 * sqm_value) + NELM_INTERCEPT_91
    else:
        nelm_value = (NELM_SLOPE_90 * sqm_value) + NELM_INTERCEPT_90
    
    # NELMをクリップ
    NELM_MIN = (NELM_SLOPE_90 * SQM_MIN) + NELM_INTERCEPT_90
    NELM_MAX = (NELM_SLOPE_91 * SQM_MAX) + NELM_INTERCEPT_91
    nelm_value = np.clip(nelm_value, NELM_MIN, NELM_MAX)

    NELM_RANGE = NELM_MAX - NELM_MIN
    if NELM_RANGE > 0:
        sky_glow_score = (nelm_value - NELM_MIN) / NELM_RANGE
    else:
        sky_glow_score = 0.0

    events = get_events_for_the_coord(
        location_name="",
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        horizon_profile=horizon_profile,
        sky_glow_score=sky_glow_score,
        starlink_instances=starlink_instances,
        station_instances=station_instances,
        weather_df=weather_df
    )

    # visibilityが高い順にソート
    events = sorted(events, key=lambda e: e.visibility, reverse=True)
    total = len(events)
    
    return {'total': total, 'events': events[offset:offset+limit]}
