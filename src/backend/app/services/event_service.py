# app/services/event_service.py
from app.schemas.event import Event
from app.schemas.trajectory import SingleTrajectory
import numpy as np
import re
from skyfield.api import Topos, load
from datetime import datetime, timedelta, timezone
from functools import lru_cache

def calc_circular_std(rads: list) -> float:
    """
    角度（ラジアン）の配列から円周標準偏差を計算する．

    Args:
        rads (list): 角度（ラジアン）の配列
    Returns:
        (float): 円周標準偏差
    """
    # 角度を単位ベクトルに変換
    x_coords = np.cos(rads)
    y_coords = np.sin(rads)

    # 重心の座標: (c_bar, s_bar)
    c_bar = np.mean(x_coords)
    s_bar = np.mean(y_coords)

    # 平均合成ベクトル長（mean resultant length）: r_bar
    r_bar = np.sqrt(c_bar**2 + s_bar**2)
    # 単位円上の点を平均しているため，0 <= r_bar <= 1．対数を取るためにゼロは回避．
    r_bar = np.clip(r_bar, 1e-12, 1.0)

    # 円周標準偏差
    circular_std_rad = np.sqrt(-2 * np.log(r_bar))
    return circular_std_rad

@lru_cache
def get_potential_trains(sat_instances, circular_std_threshold: float = 1.0):
    # TLEに記載の衛星群を国際衛星識別番号でグルーピング
    launch_groups_with_instances = {} # {グループ名: [衛星インスタンスのリスト]}
    processed_intldesg = set() # 何故か load.tle() において同じ衛星が2重に読まれるため記録

    for instance in sat_instances.values():
        intldesg = instance.model.intldesg # 国際衛星識別番号
        if intldesg in processed_intldesg:
            continue
        
        launch_group = re.search(r'\d+', intldesg).group()
        launch_groups_with_instances.setdefault(launch_group, []) # キーが存在しない時のみ空のリストをセット
        launch_groups_with_instances[launch_group].append(instance)

        # 処理が成功したら国際衛星識別番号を記録
        processed_intldesg.add(intldesg)
    
    # トレイン状態にある可能性が高いグループを特定
    launch_groups_in_train_form = {}

    for group_name, instances in launch_groups_with_instances.items():
        # 手動フィルタ
        ng_list = ['21059', '24065'] # スターリンク専用
        if group_name in ng_list:
            continue

        # 打ち上げ年フィルタ

        # TLEの使用は，そもそも1957-2056年に限定されていると推察される．
        # よって，打ち上げ年の上2桁の補完に57年ルールを適用する．
        # https://www.space-track.org/documentation#tle
        launch_year_2_digit = int(group_name[0:2])
        if launch_year_2_digit >= 57:
            launch_year_4_digit = 1900 + launch_year_2_digit
        else:
            launch_year_4_digit = 2000 + launch_year_2_digit
        
        # 今年か去年のみが通過
        current_year = datetime.now().year
        if launch_year_4_digit < (current_year - 1):
            continue

        # グループ内の全衛星から平均近点角（ラジアン）を抽出
        mean_anomalies_rad = [instance.model.mo for instance in instances]
        circular_std = calc_circular_std(mean_anomalies_rad)

        if circular_std < circular_std_threshold:
            launch_groups_in_train_form[group_name] = instances

    return launch_groups_in_train_form

@lru_cache
def get_iss_as_a_group_member(sat_instances, iss_intldesgs: list[str] = ['98067A', '21066A']):
    for instance in sat_instances.values():
        intldesg = instance.model.intldesg # 国際衛星識別番号
        if intldesg in iss_intldesgs:
            launch_group = re.search(r'\d+', intldesg).group()
            return {launch_group: [instance]}

    return {}

@lru_cache(maxsize=128)
def get_events_for_the_coord(
        location_name: str | None, # スポット以外の場合に渡す事を禁ずる．
        lat: float,
        lon: float,
        horizon_profile: list[float] | None,
        sky_glow_score: float | None,
        elevation_m: float | None,
        starlink_instances, # この関数はルーターから繰り返し呼ばれるため，ファイルI/Oはルーターに任せる．
        station_instances
    ) -> list[Event]:
    """
    単一の座標に対して，観測可能なイベントのリストを取得する．
    """
    # バッチ処理済みのスポットであるにも関わらず，静的スコアが欠損している場合はスキップする．
    if location_name and (not horizon_profile or not sky_glow_score):
        return []
    
    # 計算対象にする衛星の国際衛星識別符号を特定
    target_launch_groups = {}
    target_launch_groups.update(get_potential_trains(sat_instances=starlink_instances))
    target_launch_groups.update(get_iss_as_a_group_member(sat_instances=station_instances))

    # 処理の軽量化のためグループごとに適当な1機を抽出
    group_to_representative_sat = {group_name: instances[0] for group_name, instances in target_launch_groups.items()}

    # 打ち上げグループごとにイベントを計算
    ts = load.timescale()
    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=7))
    # tz = timezone(timedelta(hours=9))

    # 観測者の位置は，ライブラリの設定の関係から，測心座標で設定する．（earth + Topos にはしない．）
    spot_pos = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

    eph = load('de421.bsp')
    sun, earth = eph['sun'], eph['earth']

    trajectories_by_launch_group = {}
    for group_name, representative_sat in group_to_representative_sat.items():
        # 衛星の最大仰角（altitude_degrees）が10度以上になるパスを検索
        t, events = representative_sat.find_events(spot_pos, t0, t1, altitude_degrees=10.0)

        sun_alt = (earth + spot_pos).at(t).observe(sun).apparent().altaz()[0].degrees # 太陽高度のリスト
        sun_lit = representative_sat.at(t).is_sunlit(eph) # 衛星に太陽光が当たっているかの真偽値のリスト

        trajectories_for_current_sat: list[SingleTrajectory] = []
        pre_event_num = 999
        current_trajectory: SingleTrajectory | None = None
        for ti, event, s_alt, s_lit in zip(t, events, sun_alt, sun_lit):
            if event < pre_event_num:
                if current_trajectory:
                    trajectories_for_current_sat.append(current_trajectory)
                current_trajectory = SingleTrajectory()
                
            current_trajectory.list_timestamp_utc[event] = ti.utc_datetime()
            current_trajectory.list_sun_alt[event] = s_alt
            current_trajectory.list_sun_lit[event] = s_lit
                
            pre_event_num = event
        trajectories_for_current_sat.append(current_trajectory) # 最後の軌跡を追加

        # フィルタ
        filtered_trajectories = []
        for trajectory in trajectories_for_current_sat:
            # タイムスタンプが3つ全て揃っているか？（揃っていないイベントは既に始まってしまっているため．）
            has_all_timestamps = all(timestamp for timestamp in trajectory.list_timestamp_utc)
            # 太陽高度が-6度以下になる瞬間があるか？
            is_dark_enough = any(s_alt < -6.0 for s_alt in trajectory.list_sun_alt)
            # 衛星が太陽光に照らされている瞬間があるか？
            is_sunlit = any(sun_lit for sun_lit in trajectory.list_sun_lit)

            # 全ての条件を満たす場合のみ、新しいリストに追加
            if has_all_timestamps and is_dark_enough and is_sunlit:
                filtered_trajectories.append(trajectory)
            
        trajectories_by_launch_group[group_name] = filtered_trajectories

    return
