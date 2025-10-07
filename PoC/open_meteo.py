import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

# 実際にこのロジックを使用する場合は「責務の分離」に留意すること．
def calc_cloud_visibility_score(lat: float, lon: float) -> tuple[float, float, float]:
    """
    Open-Meteo APIから天気情報を取得し，雨スコア・雲量スコア・視程スコアを計算する．

    Returns:
        (float, float, float): 雨スコア・雲量スコア・視程スコア
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
    
    # 現在時刻に最も近い未来の予報を取得
    now = datetime.now(ZoneInfo(data['timezone']))
    future_forecasts = df[df['time'] >= now]
    if future_forecasts.empty:
        print("WARN: 現在時刻以降の予報が見つかりません。")
        return 0.0, 0.0, 0.0
    
    current_weather = future_forecasts.iloc[0]

    print(current_weather)
    print()
    
    precipitation = current_weather['precipitation']
    cloud_cover = current_weather['cloud_cover']
    visibility = current_weather['visibility']

    # 雨スコア
    if precipitation > 0.0: # 雨が降っていれば即ゼロ
        rain_score = 0.0
    else:
        rain_score = 1.0
    
    # 雲量スコア
    cloud_score = 1.0 - (cloud_cover / 100.0)
    
    # 視程スコア
    VIS_MIN = 5000.0  # これ以下はスコア0 (5km)
    VIS_MAX = 24140.0 # これ以上はスコア1 (24.14km)
    visibility_score = (visibility - VIS_MIN) / (VIS_MAX - VIS_MIN)
    visibility_score = np.clip(visibility_score, 0, 1) # 0.0〜1.0の範囲に収める

    return rain_score, cloud_score, visibility_score

lat, lon = 34.40875966610568, 132.72206522616142
print(calc_cloud_visibility_score(lat=lat, lon=lon))
