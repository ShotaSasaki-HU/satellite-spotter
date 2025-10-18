# app/services/score_service.py
import numpy as np
from skyfield.api import Topos, EarthSatellite, Timescale
from skyfield.jpllib import SpiceKernel
from app.core.config import Settings

def calc_visible_time_ratio(
        pass_event: dict,
        satellite: EarthSatellite,
        spot_pos: Topos,
        horizon_profile: list[float] | None,
        elevation_m: float,
        ts: Timescale,
        eph: SpiceKernel,
        settings: Settings) -> float:
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

def calc_event_score(
        pass_event: dict,
        satellite: EarthSatellite,
        spot_pos: Topos,
        horizon_profile: list[float] | None,
        sqm_value: float | None,
        elevation_m: float,
        ts: Timescale,
        eph: SpiceKernel,
        settings: Settings) -> dict:
    """
    1つのイベントに対して，地形・光害・気象を考慮した最終スコアを計算する．
    """
    # 可視時間割合

    # 光害スコア（SQM値とボートル・スケールにより夜空の暗さを評価）

    # 月相スコア（月の満ち欠け）

    # 気象スコア（観測日時における降水・雲量・視程の予報スコア）

    return
