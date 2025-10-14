# scripts/add_sky_glow_score.py

from pathlib import Path
import pandas as pd
import rasterio
import pyproj
import numpy as np
from tqdm import tqdm

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "観測候補地点"

def calc_sky_glow_score(
        path_nighttime_light: str,
        observer_lat: float,
        observer_lon: float,
        search_width: float = 100000.0, # 走査範囲の一辺の長さ（m）
        resolution: float = 500.0 # 格子の解像度（m），VIIRSの解像度は500（m）
    ):
    """
    観測地点を中心とした格子状の領域を走査し，スカイグロウ（光害）のスコアを計算する．
    スコアは各光源の「( 放射輝度 / 距離^2 ) * 面積」の総和となる．
    """
    # 格子の準備
    geod = pyproj.Geod(ellps='WGS84') # WGS84測地系に基づく測地線計算オブジェクト
    num_cells_per_side = int(search_width / resolution)

    if num_cells_per_side % 2 == 0:
        num_cells_per_side += 1

    # 格子点の中心座標に対応する，観測者からの相対位置の数列
    offsets = np.linspace(
        -search_width / 2,
        search_width / 2,
        num_cells_per_side,
        endpoint=True
    )

    # 放射輝度を取得するための座標リスト
    coords_to_sample = []
    # 各格子点の距離を保持するリスト
    distances = [] 

    # 全ての格子点を走査して2つのリストを作成
    for y_offset in offsets:
        for x_offset in offsets:
            # 格子中心までの距離と方位を計算
            dist = np.sqrt(x_offset**2 + y_offset**2)

            # 中央の格子を特別に扱う．
            is_center_cell = (dist == 0)
            if is_center_cell:
                # print("Is center cell!")
                dist = resolution / 2 # ゼロ除算を避けるための有効距離を適当に設定

            azimuth = (np.degrees(np.arctan2(x_offset, y_offset)) + 360) % 360

            # 中央のセルの場合は，観測者の座標をそのまま使う．
            if is_center_cell:
                lon, lat = observer_lon, observer_lat
            else:
                # 観測者からオフセット分離れた格子中心の緯度経度を計算
                lon, lat, back_azimuth = geod.fwd(observer_lon, observer_lat, azimuth, dist)

            coords_to_sample.append((lon, lat)) # rasterioのsampleメソッドには，座標をlon, latの順で渡す事に注意！
            distances.append(dist)

    # 光害スコアの計算
    with rasterio.open(path_nighttime_light) as src:
        if src is None:
            print("ERROR: Nighttime light dataset not available.")
            return 0.0

        sky_glow_score_sum = 0.0 # スカイグロウスコアの合計
        cell_area = resolution ** 2 # 1格子あたりの面積

        radiance_results = list(src.sample(coords_to_sample))
        radiances = [result[0] for result in radiance_results] # 放射輝度リスト
        for radiance, dist in zip(radiances, distances):
            if radiance is None or np.isnan(radiance) or radiance < 0:
                radiance = 0.0

            contribution = (radiance / (dist ** 2)) * cell_area
            sky_glow_score_sum += contribution

    return sky_glow_score_sum

def main():
    print("光害スコアをCSVに追記します．")

    try:
        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            df = pd.read_csv(csv_path, encoding='utf-8', header=0)
            print(f"{len(df)}件のスポットの光害スコアを計算中...")

            path_viirs_tiff = "/Volumes/iFile-1/satellite-spotter/VNL_npp_2024_global_vcmslcfg_v2_c202502261200.median_masked.dat.tif"

            # tqdmとpandasを連携・プログレスバーの説明を設定
            tqdm.pandas(desc="Calculating Sky Glow Score")

            # 1行ずつcalc_sky_glow_score関数を実行
            df['sky_glow_score'] = df.progress_apply(
                lambda row: calc_sky_glow_score(
                    path_nighttime_light=path_viirs_tiff,
                    observer_lat=row['latitude'],
                    observer_lon=row['longitude']
                ),
                axis=1 # axis=1 で行ごとに処理
            )

            print(f"{csv_path} を保存中...")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print('---')

        print("光害スコアの追記が正常に完了しました．")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
