import jismesh.utils as ju
import os
import rasterio
from functools import lru_cache
import numpy as np

def get_meshcode_by_coord(lat, lon, n):
    """
    緯度・経度に対応するn次メッシュを返す．
    ・1次メッシュ：約80km四方
    ・2次メッシュ：約10km四方
    ・3次メッシュ：約1km四方
    """
    return ju.to_meshcode(lat, lon, n)

@lru_cache(maxsize=128)
def get_dsm_dataset(tertiary_meshcode):
    """
    3次メッシュコードに対応するrasterioデータセットを返す．
    結果は，LRUキャッシュによってメモリに保持される．
    """
    print(f"DEBUG: Cache miss! Opening dsm file for {tertiary_meshcode}.")

    # メッシュコードが3次メッシュであるか確認
    if len(str(tertiary_meshcode)) != 8:
        raise ValueError(f"Invalid tertiary meshcode: {tertiary_meshcode}. It must be 8 digits.")
    
    tertiary_meshcode = str(tertiary_meshcode)
    first = tertiary_meshcode[0:4]
    second = tertiary_meshcode[4:6]
    third = tertiary_meshcode[6:]
    path_dsm_tiff = f"/Volumes/iFile-1/DEM1A/{first}/{first}-{second}/FG-GML-{first}-{second}-{third}-DEM1A-20250502.tif"

    if not os.path.exists(path_dsm_tiff):
        return None
    else:
        return rasterio.open(path_dsm_tiff)

def get_elevation_by_coord(lat: float, lon: float) -> float:
    """
    任意の緯度経度に対応するGeoTIFFファイルを見つけて標高値を返す．
    """
    # 緯度経度から3次メッシュコードを計算
    tertiary_meshcode = get_meshcode_by_coord(lat=34.4223, lon=132.7441, n=3)
    if not tertiary_meshcode:
        return np.nan
    
    # 3次メッシュコードに対応するrasterioデータセットを取得（キャッシュあり）
    dataset = get_dsm_dataset(tertiary_meshcode)
    if dataset is None:
        print(f"DEBUG: DSM file for meshcode {tertiary_meshcode} not found.")
        return np.nan
    
    # 指定した座標の標高値を取得
    try:
        # .sample()はジェネレータを返すため，next()で最初の（そして唯一の）結果を取り出す．
        # その結果はNumPy配列なので，[0]で中の数値を取り出す．
        # dataset.sample()には [(経度, 緯度)] の順で座標を渡すことに注意！
        elevation = next(dataset.sample([(lon, lat)]))[0]
        return elevation
    except IndexError:
        return np.nan

target_lat = 34.4223
target_lon = 132.7441

print("--- 1回目の標高取得 ---")
elevation1 = get_elevation_by_coord(target_lat, target_lon)
if not np.isnan(elevation1):
    print(f"✅ 標高: {elevation1:.2f} m")
else:
    print("❌ 標高データを取得できませんでした。")

print("\n--- 2回目の標高取得（キャッシュが効くはず） ---")
elevation2 = get_elevation_by_coord(target_lat, target_lon)
if not np.isnan(elevation2):
    print(f"✅ 標高: {elevation2:.2f} m")
else:
    print("❌ 標高データを取得できませんでした。")
