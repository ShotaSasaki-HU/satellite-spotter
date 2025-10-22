# app/routers/trajectories.py
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from skyfield.api import Topos
import numpy as np
from app.core.config import Settings, get_settings
from app.schemas.trajectory import Position, Trajectory, TrajectoryResponse
from app.services.dem_service import get_elevations_by_coords
from app.services.sat_service import SatDataService, get_sat_data_service

router = APIRouter()
@router.get("/api/v1/trajectories", response_model=TrajectoryResponse)
def get_trajectory_details(
        location_name: str,
        start_time: datetime,
        end_time: datetime,
        lat: float,
        lon: float,
        international_designators: list[str],
        settings: Settings = Depends(get_settings),
        sat_service: SatDataService = Depends(get_sat_data_service)):
    """
    指定された期間における，指定された衛星群の時系列的な位置を返す．
    """
    intldesg_to_sat = sat_service.get_all_satellites()

    # 国際衛星識別番号で指定されたインスタンスを抽出
    target_instances = []
    for intldesg in international_designators:
        instance = intldesg_to_sat.get(intldesg, None) # O(1)で高速に検索
        if instance:
            target_instances.append(instance)
    
    if not target_instances:
        raise HTTPException(status_code=404, detail="指定された国際衛星識別番号の衛星が見つかりません．")

    # 開始時刻と終了時刻から時刻列を作成
    ts = sat_service.get_timescale()
    t_start = ts.from_datetime(start_time)
    t_end = ts.from_datetime(end_time)
    # 地球時（Terrestrial Time）のユリウス日の数値配列に変換してlinspace
    SAMPLING_COUNT = 30
    tt_values = np.linspace(t_start.tt, t_end.tt, num=SAMPLING_COUNT, endpoint=True)
    # skyfield.timelib.Timeの時刻列
    t = ts.tt_jd(tt_values)

    # Toposの作成
    elevation_m = get_elevations_by_coords(coords=[{'lat': lat, 'lon': lon}],
                                           settings=settings)[0]
    if elevation_m < -1000 or np.isnan(elevation_m):
        print(f"⚠️ 警告: 観測地点 ({lat}, {lon}) の標高が取得できませんでした．")
        return {'location_name': location_name, 'trajectories': []}
    
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

    trajectories = []
    for t_current in t:
        positions = []
        for sat in target_instances:
            alt, az, distance = (sat - observer).at(t_current).altaz()
            posi = Position(
                international_designator=sat.model.intldesg,
                az=az.degrees,
                alt=alt.degrees
            )
            positions.append(posi)

        trajectory = Trajectory(
            timestamp=t_current.astimezone(timezone.utc).isoformat(),
            positions=positions
        )
        trajectories.append(trajectory)

    return TrajectoryResponse(location_name=location_name, trajectories=trajectories)
