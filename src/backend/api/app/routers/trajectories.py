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
        location_name: str = Query(...),
        start_time: datetime = Query(...),
        end_time: datetime = Query(...),
        lat: float = Query(...),
        lon: float = Query(...),
        international_designators: list[str] = Query(..., description="...&international_designators=25225A&international_designators=25212A..."),
        settings: Settings = Depends(get_settings),
        sat_service: SatDataService = Depends(get_sat_data_service)):
    """
    指定された期間における，指定された衛星群の時系列的な位置を返す．
    """
    # 国際衛星識別番号で指定されたインスタンスを抽出
    target_instances = []
    intldesg_to_sat = sat_service.get_all_satellites()
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
    # skyfield.timelib.Timeの時刻配列
    t = ts.tt_jd(tt_values)

    # Toposの作成
    elevation_m = get_elevations_by_coords(coords=[{'lat': lat, 'lon': lon}],
                                           settings=settings)[0]
    if elevation_m < -1000 or np.isnan(elevation_m):
        print(f"⚠️ 警告: 観測地点 ({lat}, {lon}) の標高が取得できませんでした．")
        return TrajectoryResponse(location_name=location_name, trajectories=[])
    
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

    # ベクトルを活用したSkyfieldでの計算
    ## 衛星ごとに全時刻の位置を一括計算して辞書に格納
    all_positions_by_sat: dict[str, list[dict]] = {}
    for sat in target_instances:
        # 時刻配列't'を使ってベクトル計算
        alt, az, distance = (sat - observer).at(t).altaz()

        positions = [
            {'az': az.degrees[i], 'alt': alt.degrees[i]} for i in range(SAMPLING_COUNT)
        ]
        all_positions_by_sat[sat.model.intldesg] = positions
    
    ## スキーマに合わせてデータを再構築
    trajectories = []
    for i, t_current in enumerate(t, start=0):
        positions_at_t = []

        # クエリで指定された順序を維持してループ
        for intldesg in international_designators:
            sat_pos_data = all_positions_by_sat.get(intldesg, None)

            if sat_pos_data:
                pos_at_i = sat_pos_data[i]
                posi = Position(
                    international_designator=intldesg,
                    az = pos_at_i['az'],
                    alt = pos_at_i['alt']
                )
                positions_at_t.append(posi)
        
        trajectory = Trajectory(
            timestamp=t_current.astimezone(timezone.utc).isoformat(),
            positions=positions_at_t
        )
        trajectories.append(trajectory)

    return TrajectoryResponse(location_name=location_name, trajectories=trajectories)
