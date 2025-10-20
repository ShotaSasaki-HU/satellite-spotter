# app/services/event_service.py
import numpy as np
import re
from skyfield.api import Topos, load, EarthSatellite
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from app.schemas.event import Event
import pandas as pd
import requests
from app.services.score_service import calc_event_score

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

def get_iss_as_a_group_member(sat_instances, iss_intldesgs: list[str] = ['98067A', '21066A']):
    for instance in sat_instances.values():
        intldesg = instance.model.intldesg # 国際衛星識別番号
        if intldesg in iss_intldesgs:
            launch_group = re.search(r'\d+', intldesg).group()
            return {launch_group: [instance]}

    return {}

def get_raw_pass_events(satellite: EarthSatellite, spot_pos,
                        t0, t1, min_required_alt_deg = 10.0) -> list[dict]:
    """
    1つの衛星について，指定期間内の生の通過イベントを抽出する．
    """
    t, events = satellite.find_events(spot_pos, t0, t1, altitude_degrees=min_required_alt_deg)

    # イベントを「昇る（0）」「天頂（１）」「沈む（２）」の組にまとめる．
    pass_events = []
    current_pass = {}
    for ti, event_code in zip(t, events):
        if event_code == 0:
            current_pass = {'rise_time': ti}
        elif event_code == 1:
            current_pass['peak_time'] = ti
        elif event_code == 2:
            current_pass['set_time'] = ti
            pass_events.append(current_pass)
            current_pass = {}

    return pass_events

def filter_visible_events(pass_events, satellite: EarthSatellite, spot_pos, eph, ts) -> list[dict]:
    """
    天文学的な条件（観測地点の暗さ・衛星の被照）でイベントを絞り込む．
    """
    visible_events = []
    sun, earth = eph['sun'], eph['earth']

    for pass_event in pass_events:
        # 3つ全てのタイムスタンプが存在するか？（欠けているとスコアリングが困難）
        has_full_timestamp = len(pass_event) == 3

        # 「太陽高度が-6度以下」かつ「衛星が太陽光に照らされている」瞬間があるか？
        t_list = [time.tt for time in pass_event.values()]
        t = ts.tt_jd(t_list)
        sun_alt = (earth + spot_pos).at(t).observe(sun).apparent().altaz()[0].degrees # 太陽高度のリスト
        is_dark_enough = sun_alt <= -6 # 太陽高度が-6度以下であるかの真偽値リスト
        is_sun_lit = satellite.at(t).is_sunlit(eph) # 衛星に太陽光が当たっているかの真偽値リスト
        bright_moment_exists = any(is_bright_moment for is_bright_moment in (is_dark_enough & is_sun_lit))

        if has_full_timestamp and bright_moment_exists:
            visible_events.append(pass_event)
    
    return visible_events

def get_weather_dataframe(spot_pos: Topos):
    # Open-Meteo APIのエンドポイントとパラメータ
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": spot_pos.latitude.degrees,
        "longitude": spot_pos.longitude.degrees,
        "elevation": spot_pos.elevation.m,
        "hourly": "precipitation,cloud_cover,visibility",
        "timezone": "GMT+0" # ほぼUTCと一致
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # エラーがあれば例外を発生
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: APIへのリクエストに失敗しました: {e}")
        return 0.0, {}
    
    df = pd.DataFrame(data['hourly'])
    df['time'] = pd.to_datetime(df['time']).dt.tz_localize('utc')

    return df

def get_events_for_the_coord(
        location_name: str, # スポット以外の場合は空文字列を渡す．
        lat: float,
        lon: float,
        elevation_m: float,
        horizon_profile: list[float],
        sky_glow_score: float,
        starlink_instances, # ファイルI/Oはルーターに任せる．
        station_instances) -> list[Event]:
    """
    単一の座標に対して，観測可能なイベントのリストを取得する．
    """
    # 静的スコアが欠損している場合はスキップする．
    if not elevation_m or not horizon_profile or not sky_glow_score:
        print(f"WARNING: get_events_for_the_coord関数において，観測地点 ({lat}, {lon}) の静的スコアが不足しています．観測イベントの取得をスキップします．")
        return []
    
    # 計算対象にする衛星の国際衛星識別符号を特定
    launch_groups_to_sats = {}
    launch_groups_to_sats.update(get_potential_trains(sat_instances=starlink_instances))
    launch_groups_to_sats.update(get_iss_as_a_group_member(sat_instances=station_instances))

    # 時刻・検索期間設定
    ts = load.timescale()
    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=7))

    # 観測値設定
    spot_pos = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

    # 天体暦設定
    eph = load('de421.bsp')

    # 天気予報のデータフレームを取得
    weather_df = get_weather_dataframe(spot_pos=spot_pos)

    events = []
    for group_name, instances in launch_groups_to_sats.items():
        repre_sat = instances[0] # 処理の軽量化のため代表衛星を適当に定義

        # 生の天球イベントを取得
        raw_passes = get_raw_pass_events(satellite=repre_sat, spot_pos=spot_pos, t0=t0, t1=t1)
        # 天文学的条件でフィルタ
        visible_passes = filter_visible_events(pass_events=raw_passes, satellite=repre_sat,
                                               spot_pos=spot_pos, eph=eph, ts=ts)
        
        for pass_event in visible_passes:
            scores = calc_event_score(
                pass_event=pass_event,
                satellite=repre_sat,
                spot_pos=spot_pos,
                horizon_profile=horizon_profile,
                sky_glow_score=sky_glow_score,
                ts=ts,
                eph=eph,
                weather_df=weather_df
            )

            if 'STARLINK' in repre_sat.name:
                event_type = 'スターリンクトレイン'
            elif 'ISS' in repre_sat.name:
                event_type = '国際宇宙ステーション（ISS）'
            else:
                event_type = '不明'
            
            intldesg = repre_sat.model.intldesg

            event = Event(
                location_name=location_name,
                start_time=pass_event['rise_time'].astimezone(timezone.utc).isoformat(),
                end_time=pass_event['set_time'].astimezone(timezone.utc).isoformat(),
                visibility=scores['visibility'],
                event_type=event_type,
                lat=lat,
                lon=lon,
                international_designator=intldesg
            )

            events.append(event)

    return events
