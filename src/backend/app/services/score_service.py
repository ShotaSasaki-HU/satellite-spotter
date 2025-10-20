# app/services/score_service.py
import numpy as np
from skyfield.api import Topos, EarthSatellite, Timescale
from skyfield.jpllib import SpiceKernel
import pandas as pd

def calc_visible_time_ratio(
        pass_event: dict,
        satellite: EarthSatellite,
        spot_pos: Topos,
        horizon_profile: list[float],
        ts: Timescale,
        eph: SpiceKernel) -> float:
    """
    1つのイベントに対して，地形と天文学的な条件（観測地点の暗さ・衛星の被照）から，イベント期間に対する衛星の可視時間割合を計算する．
    """
    t_rise = pass_event['rise_time']
    t_set = pass_event['set_time']
    # 地球時（Terrestrial Time）のユリウス日の数値配列に変換してlinspace
    tt_values = np.linspace(t_rise.tt, t_set.tt, num=10, endpoint=True)
    # skyfield.timelib.Timeの時刻列
    t = ts.tt_jd(tt_values)

    # 1. 稜線や水地平線に衛星が隠れていないか？

    # 3つの「配列オブジェクト」をタプルとして受け取る．
    alt_az_dist_tuple = (satellite - spot_pos).at(t).altaz()
    # 各オブジェクトからPythonが処理できる「数値の配列」を取り出す．
    sat_altitudes_deg: np.ndarray = alt_az_dist_tuple[0].degrees
    sat_azimuths_deg: np.ndarray = alt_az_dist_tuple[1].degrees

    # 衛星の方位角[0:360)を，稜線プロファイルのインデックス[0:len(horizon_profile)-1]に変換する．
    horizon_profile = np.array(horizon_profile)
    len_horizon_profile = len(horizon_profile)
    indices = np.floor((sat_azimuths_deg / 360.0) * len_horizon_profile).astype(int)
    indices = np.clip(indices, 0, len_horizon_profile - 1)

    horizon_altitudes_deg = horizon_profile[indices] # 衛星の方位角に対応する稜線高度

    is_foreground: np.ndarray = sat_altitudes_deg > horizon_altitudes_deg

    # 2. 観測地点の暗さ
    sun, earth = eph['sun'], eph['earth']
    sun_alt: np.ndarray = (earth + spot_pos).at(t).observe(sun).apparent().altaz()[0].degrees # 太陽高度のリスト
    is_dark_enough: np.ndarray = sun_alt <= -6 # 太陽高度が-6度以下であるかの真偽値リスト

    # 3. 衛星の被照
    is_sun_lit: np.ndarray = satellite.at(t).is_sunlit(eph) # 衛星に太陽光が当たっているかの真偽値リスト

    return (is_foreground & is_dark_enough & is_sun_lit).mean() # Trueの割合

def calc_moon_fraction_illuminated(
        pass_event: dict,
        spot_pos: Topos,
        eph: SpiceKernel):
    """
    1つのイベントに対して，月が照らされている割合を計算する．
    """
    t_peak = pass_event['peak_time']
    sun, moon, earth = eph['sun'], eph['moon'], eph['earth']

    # 月が地平線の下ならば，明るさに関わらず影響はゼロ．
    moon_alt = (earth + spot_pos).at(t_peak).observe(moon).apparent().altaz()[0].degrees
    if moon_alt < 0:
        return 1.0
    
    # What fraction of a spherical body is illuminated by the sun.
    moon_fract_illumi = (earth + spot_pos).at(t_peak).observe(moon).apparent().fraction_illuminated(sun)

    return 1.0 - moon_fract_illumi

def get_meteorological_score(pass_event: dict, weather_df: pd.DataFrame) -> tuple[float, float, float]:
    """
    Open-Meteo APIから天気情報を取得し，雨スコア・雲量スコア・視程スコアを計算する．

    Returns:
        (float, float, float): 雨スコア・雲量スコア・視程スコア
    """
    df = weather_df

    # パスイベント開始時刻に最も近い未来の予報を取得
    t_rise = pass_event['rise_time'].utc_datetime()
    future_forecasts = df[df['time'] >= t_rise]
    if future_forecasts.empty:
        print("WARN: 現在時刻以降の予報が見つかりません。")
        return 0.0, 0.0, 0.0
    
    current_weather = future_forecasts.iloc[0]

    precipitation = current_weather['precipitation']
    cloud_cover = current_weather['cloud_cover']
    met_visibility = current_weather['visibility']

    # 雨スコア
    if precipitation > 0.0: # 雨が降る予報ならば即ゼロ
        rain_score = 0.0
    else:
        rain_score = 1.0
    
    # 雲量スコア
    cloud_score = 1.0 - (cloud_cover / 100.0)
    
    # 視程スコア
    VIS_MIN = 5000.0  # これ以下はスコア0 (5km)
    VIS_MAX = 24140.0 # これ以上はスコア1 (24.14km)
    met_visibility_score = (met_visibility - VIS_MIN) / (VIS_MAX - VIS_MIN)
    met_visibility_score = np.clip(met_visibility_score, 0, 1) # 0.0-1.0の範囲にクリップ

    return rain_score, cloud_score, met_visibility_score

def calc_event_score(
        pass_event: dict,
        satellite: EarthSatellite,
        spot_pos: Topos,
        horizon_profile: list[float],
        sky_glow_score: float,
        ts: Timescale,
        eph: SpiceKernel,
        weather_df: pd.DataFrame) -> dict:
    """
    1つのイベントに対して，地形・光害・気象を考慮した最終スコアを計算する．
    """
    scores = {}

    # 可視時間割合
    visible_time_ratio = calc_visible_time_ratio(pass_event=pass_event, satellite=satellite, spot_pos=spot_pos,
                                                 horizon_profile=horizon_profile, ts=ts, eph=eph)
    scores['visible_time_ratio'] = visible_time_ratio

    # 光害スコア（SQM値とボートル・スケールにより夜空の暗さを評価）
    scores['sky_glow_score'] = sky_glow_score

    # 月相スコア（月の満ち欠け）
    moon_fract_illumi = calc_moon_fraction_illuminated(pass_event=pass_event, spot_pos=spot_pos, eph=eph)
    scores['moon_fract_illumi'] = moon_fract_illumi

    # 気象スコア（観測日時における降水・雲量・視程の予報スコア）
    rain_score, cloud_score, met_visibility_score = get_meteorological_score(pass_event=pass_event, weather_df=weather_df)
    scores['rain_score'] = rain_score
    scores['cloud_score'] = cloud_score
    scores['met_visibility_score'] = met_visibility_score

    # 衛星の満ち欠け？

    # 不快度スコア？

    # 最終スコアの計算（全スコアの総積）
    visibility = np.prod(list(scores.values()))
    scores['visibility'] = visibility

    return scores
