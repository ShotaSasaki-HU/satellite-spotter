# app/services/star_service.py
from datetime import datetime
from app.services.astro_service import AstroDataService
from skyfield.api import Topos, Time

# https://www.pas.rochester.edu/~emamajek/WGSN/IAU-CSN.txt
HIP_TO_NAME = {
    32349: "シリウス",        # 大犬座
    30438: "カノープス",      # りゅうこつ座
    71683: "アルファ・ケンタウリ", # ケンタウルス座
    69673: "アークトゥルス",    # うしかい座
    91262: "ベガ（織姫星）",     # こと座
    24608: "カペラ",          # ぎょしゃ座
    24436: "リゲル",          # オリオン座
    37279: "プロキオン",      # こいぬ座
    7588:  "アケルナル",      # エリダヌス座
    27989: "ベテルギウス",    # オリオン座
    68702: "ハダル",          # ケンタウルス座
    97649: "アルタイル（彦星）", # わし座
    60718: "アクルックス",    # みなみじゅうじ座
    21421: "アルデバラン",    # おうし座
    80763: "アンタレス",      # さそり座
    65474: "スピカ",          # おとめ座
    37826: "ポルックス",      # ふたご座
    113368: "フォーマルハウト", # みなみのうお座
    102098: "デネブ",         # はくちょう座
    62434: "ミモザ",          # みなみじゅうじ座
    49669: "レグルス",        # しし座
    36850: "カストル",        # ふたご座
    11767: "ポラリス（北極星）", # こぐま座
}

def get_visible_stars(
        lat: float,
        lon: float,
        time_utc: datetime,
        astro_service: AstroDataService) -> list[dict]:
    """
    指定された時刻・地点において，地平線上にある恒星のリストを一括計算して返す．
    """
    ts = astro_service.get_timescale()
    t: Time = ts.from_datetime(time_utc)

    eph = astro_service.get_ephemeris()
    earth = eph['earth']
    spot_pos = Topos(latitude_degrees=lat, longitude_degrees=lon)

    # forループを回さず，観測者から見た全恒星の相対位置を一発の行列計算で算出する．
    bright_stars = astro_service.get_bright_stars()
    alt, az, _ = (earth + spot_pos).at(t).observe(bright_stars).apparent().altaz()
    alt_deg = alt.degrees
    az_deg = az.degrees

    # 地平線より上にある星だけの真偽値リストを作成
    visible_mask = alt_deg > 0

    visible_stars = []
    star_hip_ids = astro_service.get_star_hip_ids()
    star_magnitudes = astro_service.get_star_magnitudes()
    for i, is_visible in enumerate(visible_mask):
        if is_visible:
            hip_id = star_hip_ids[i]
            star_name = HIP_TO_NAME.get(hip_id, "") # HIP番号を固有名に変換

            visible_stars.append({
                "star_name": star_name,
                "az": float(az_deg[i]),
                "alt": float(alt_deg[i]),
                "magnitude": float(star_magnitudes[i])
            })

    return visible_stars
