import requests
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def calc_weather_score(lat: float, lon: float) -> tuple[float, dict]:
    """
    Open-Meteo APIから天気情報を取得し，天候スコアを計算する．

    Returns:
        (float, dict): 総合スコアと，その内訳の辞書
    """
    # Open-Meteo APIのエンドポイントとパラメータ
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,cloud_cover,visibility",
        "timezone": "auto" # 座標に合わせて
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # エラーがあれば例外を発生
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: APIへのリクエストに失敗しました: {e}")
        return 0.0, {}
    
    df = pd.DataFrame(data['hourly'])
    df['time'] = pd.to_datetime(df['time']).dt.tz_localize(ZoneInfo(data['timezone']))

    print(df)
    print()
    
    # 現在時刻に最も近い未来の予報を取得
    now = datetime.now(ZoneInfo(data['timezone']))
    future_forecasts = df[df['time'] >= now]
    if future_forecasts.empty:
        print("WARN: 現在時刻以降の予報が見つかりません。")
        return 0.0, {}
    
    current_weather = future_forecasts.iloc[0]
    
    precipitation = current_weather['precipitation']
    cloud_cover = current_weather['cloud_cover']
    visibility = current_weather['visibility']

    # --- スコアリング ---
    # 1. 雨のチェック
    if precipitation > 0.0:
        score = 0.0
        details = {
            "降水量(mm)": precipitation,
            "雲量(%)": cloud_cover,
            "視程(m)": visibility,
            "判定": "雨のため観測不可"
        }
        return score, details

    # 2. 雲係数の計算
    cloud_factor = 1.0 - (cloud_cover / 100.0)
    
    # 3. 透明度係数の計算
    VIS_MIN = 5000.0  # これ以下はスコア0 (5km)
    VIS_MAX = 24140.0 # これ以上はスコア1 (24.14km)
    
    visibility_factor = (visibility - VIS_MIN) / (VIS_MAX - VIS_MIN)
    visibility_factor = max(0.0, min(1.0, visibility_factor)) # 0.0〜1.0の範囲に収める

    # 4. 総合スコアの計算
    score = cloud_factor * visibility_factor
    
    details = {
        "降水量(mm)": precipitation,
        "雲量(%)": cloud_cover,
        "視程(m)": visibility,
        "雲係数": round(cloud_factor, 2),
        "透明度係数": round(visibility_factor, 2)
    }

    return score, details

lat, lon = 33.842129580222284, 130.72070852147652
print(calc_weather_score(lat=lat, lon=lon))
