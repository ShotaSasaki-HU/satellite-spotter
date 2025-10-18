# scripts/add_elevation_m.py
import jismesh.utils as ju
import numpy as np
import rasterio
from pathlib import Path
from tqdm import tqdm
import pandas as pd

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.core.config import get_settings
settings = get_settings()

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "観測候補地点"

def get_meshcode_by_coord(lat, lon, n):
    """
    緯度・経度に対応するn次メッシュを返す．
    """
    return ju.to_meshcode(lat, lon, n)

def get_elevations_by_coords(coords: list[dict]) -> np.ndarray:
    """
    緯度経度リストに対応するGeoTIFFファイルを見つけて標高値リストを返す．
    """
    # 座標を所属するメッシュコードごとに分類（sampleメソッドの呼び出し回数を減らすため．）
    coords_by_meshcode = {}
    for i, coord in enumerate(coords, start=0):
        meshcode = get_meshcode_by_coord(lat=coord['lat'], lon=coord['lon'], n=3)
        if meshcode not in coords_by_meshcode:
            coords_by_meshcode[meshcode] = []
        # (lon, lat, 元のインデックス)のタプルで保存
        coords_by_meshcode[meshcode].append((coord['lon'], coord['lat'], i))
    
    # メッシュごとに標高データを取得
    elevations = np.full(len(coords), np.nan, dtype=float) # 結果を格納するリスト
    for meshcode, coords_with_indices in coords_by_meshcode.items():
        path_dsm = settings.get_dem_filepath(tertiary_meshcode=meshcode)
        if path_dsm is None: # TIFFファイルが存在しなければ開く処理に進まない．
            continue

        with rasterio.open(path_dsm) as src:
            # このファイルに属する座標だけをまとめてsampleに渡す．
            coords_to_sample = [(lon, lat) for lon, lat, idx in coords_with_indices]
            results = list(src.sample(coords_to_sample))
        
        # 結果を元のインデックスの位置に格納
        for i, result in enumerate(results, start=0):
            original_index = coords_with_indices[i][2]
            elevations[original_index] = result[0]
    
    return elevations

def main():
    print("スポットの標高をCSVに追記します．")

    try:
        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            df = pd.read_csv(csv_path, encoding='utf-8', header=0)
            print(f"{len(df)}件のスポットの標高値を計算中...")

            # tqdmとpandasを連携・プログレスバーの説明を設定
            tqdm.pandas(desc="Calculating Elevation")

            # 1行ずつ実行
            df['elevation_m'] = df.progress_apply(
                lambda row: get_elevations_by_coords(
                    coords=[{'lat': row['latitude'], 'lon': row['longitude']}]
                )[0],
                axis=1 # axis=1 で行ごとに処理
            )

            print(f"{csv_path} を保存中...")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print('---')

        print("標高の追記が正常に完了しました．")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
