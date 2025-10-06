import jismesh.utils as ju
import os
import rasterio
from functools import lru_cache

def get_meshcode_by_coord(lat, lon, n):
    """
    緯度・経度に対応するn次メッシュを返す．
    ・1次メッシュ：約80km四方
    ・2次メッシュ：約10km四方
    ・3次メッシュ：約1km四方
    """
    return ju.to_meshcode(lat, lon, n)

@lru_cache(maxsize=128)
def get_dsm_by_tertiary_meshcode(tertiary_meshcode):
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

tertiary_meshcode = get_meshcode_by_coord(lat=34.4223, lon=132.7441, n=3)
if tertiary_meshcode:
    # 1回目の呼び出し（ディスクからファイルを開く）
    dataset1 = get_dsm_by_tertiary_meshcode(tertiary_meshcode)
    if dataset1:
        print(f"1回目: {dataset1.name} を取得")

    # 2回目の呼び出し（キャッシュから瞬時に取得）
    dataset2 = get_dsm_by_tertiary_meshcode(tertiary_meshcode)
    if dataset2:
        print(f"2回目: {dataset2.name} を取得")
