# scripts/add_horizon_profile.py
import jismesh.utils as ju
import numpy as np
import rasterio
import pyproj
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
        path_dem = settings.get_dem_filepath(tertiary_meshcode=meshcode)
        if path_dem is None: # TIFFファイルが存在しなければ開く処理に進まない．
            continue

        with rasterio.open(path_dem) as src:
            # このファイルに属する座標だけをまとめてsampleに渡す．
            coords_to_sample = [(lon, lat) for lon, lat, idx in coords_with_indices]
            results = list(src.sample(coords_to_sample))
        
        # 結果を元のインデックスの位置に格納
        for i, result in enumerate(results, start=0):
            original_index = coords_with_indices[i][2]
            elevations[original_index] = result[0]
    
    return elevations

def calc_hidden_height(observer_height: float, distances_grid: np.ndarray) -> np.ndarray:
    """
    観測者の高さと対象までの距離から，地球の丸みで隠される高さを計算する．

    Args:
        observer_height (float): 観測者の視点の高さ（m）
        distances_grid (np.ndarray): 観測者から対象までの水平距離（m）

    Returns:
        (np.ndarray): 地球の丸みによって隠される高さ（m）
    """
    EARTH_R = 6371000.0 # 地球の半径（m）

    # 観測者の視点が0m未満の場合，水平線までの距離は0とする．（elseの式に負のobserver_heightが代入できないため．）
    observer_height = max(observer_height, 0.0)

    # 観測者の視点から水平線までの距離（厳密式）
    dist_to_horizon = np.sqrt((2 * EARTH_R * observer_height) + (observer_height ** 2))

    # 地球の丸みによって隠される高さ
    hidden_height = np.where(
        distances_grid < dist_to_horizon, # 対象が水平線より手前にある場合，地球の丸みによって対象が隠される事は無い．
        0.0,
        np.sqrt((EARTH_R ** 2) + ((distances_grid - dist_to_horizon) ** 2)) - EARTH_R
    )

    return hidden_height

def calc_viewing_angle(observer_height: float, elevations_grid: np.ndarray, distances_grid: np.ndarray) -> np.ndarray:
    """
    観測者から見た対象の仰角・俯角を計算する．（地球の丸みを考慮）

    Args:
        observer_height (float): 観測者の標高（m）
        elevations_grid (np.ndarray): 対象となる地形の標高（m）
        distances_grid (np.ndarray): 観測者から対象までの水平距離（m）

    Returns:
        (np.ndarray): 仰俯角（度）
    """
    # 地球の丸みによって隠される高さ
    hidden_height = calc_hidden_height(observer_height=observer_height, distances_grid=distances_grid)
    apparent_target_height = elevations_grid - hidden_height
    height_diff = apparent_target_height - observer_height

    # 仰角を計算
    angles_rad = np.arctan(height_diff / distances_grid)
    angles_deg = np.degrees(angles_rad)

    # 各方位（行）ごとに最大仰角を抽出
    max_angles = np.max(angles_deg, axis=1)
    
    return max_angles

def calc_horizon_profile(
        settings: Settings,
        observer_lat: float,
        observer_lon: float,
        observer_eye_height: float = 1.55,
        num_directions: int = 180,
        max_distance: float = 100000,
        num_samples: int = 100):
    """
    観測地点から360°の水地平線・稜線プロファイルを計算する．

    Args:
        observer_lat (float): 観測者の緯度
        observer_lon (float): 観測者の経度
        observer_eye_height (float): 観測者の身長による視点の高さ（m）
        num_directions (int): 走査する方位の数（解像度）
        max_distance (float): 最大探索距離（m）
        num_samples (int): 1方位あたりのサンプリング点数

    Returns:
        (np.ndarray): 各方位における最大仰角（稜線の仰角）を格納した配列
        (np.ndarray): 方位の配列
    """
    # 観測者の準備
    observer_ground_elev = get_elevations_by_coords(coords=[{'lat': observer_lat, 'lon': observer_lon}],
                                                    settings=settings)[0]
    if observer_ground_elev < -1000 or np.isnan(observer_ground_elev):
        print(f"⚠️警告: 観測地点 ({observer_lat}, {observer_lon}) の標高が取得できませんでした．スキップします．")
        empty_profile = np.full(num_directions, np.nan)
        azimuths = np.linspace(0, 360, num_directions, endpoint=False)
        return empty_profile, azimuths

    observer_height = observer_ground_elev + observer_eye_height

    # 計算パラメータの準備
    azimuths = np.linspace(0, 360, num_directions, endpoint=False) # 各方位
    distances = np.geomspace(1, max_distance, num_samples) # 各サンプリング点

    # メッシュグリッドで全ての (方位, 距離) の組み合わせをマトリックスで作成
    azimuths_grid, distances_grid = np.meshgrid(azimuths, distances, indexing='ij')

    geod = pyproj.Geod(ellps='WGS84')
    lons_grid, lats_grid, _ = geod.fwd(
        np.full_like(distances_grid, observer_lon),
        np.full_like(distances_grid, observer_lat),
        azimuths_grid,
        distances_grid
    )

    # 座標を1次元のリストにする．
    flat_lons = lons_grid.flatten()
    flat_lats = lats_grid.flatten()
    coords = [{'lat': lat, 'lon': lon} for lat, lon in zip(flat_lats, flat_lons)]

    # get_elevations_by_coordsは，同じTIFFファイルは1回しか開かない．
    flat_elevations = get_elevations_by_coords(coords, settings)

    # 標高データを元の形に戻す．
    elevations_grid = flat_elevations.reshape(distances_grid.shape)
    elevations_grid[np.isnan(elevations_grid)] = 0.0

    # 各方位ごとに最大仰角を抽出
    max_angles = calc_viewing_angle(
        observer_height=observer_height,
        elevations_grid=elevations_grid,
        distances_grid=distances_grid
    )

    return max_angles, azimuths

def main():
    print("稜線プロファイルをCSVに追記します．")

    try:
        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            df = pd.read_csv(csv_path, encoding='utf-8', header=0)
            print(f"{len(df)}件のスポットの稜線プロファイルを計算中...")

            tqdm.pandas(desc="Calculating Horizon Profile")

            # applyの結果を2つの新しい列に代入
            df[['horizon_profile_list', 'azimuths_list']] = df.progress_apply(
                lambda row: calc_horizon_profile(
                    observer_lat=row['latitude'],
                    observer_lon=row['longitude'],
                    num_directions=180,
                    max_distance=100000,
                    num_samples=1000
                ),
                axis=1,
                result_type='expand' # 戻り値が複数であるため．
            )

            # 稜線プロファイルのリストをカンマ区切りの文字列に変換する．
            df['horizon_profile'] = df['horizon_profile_list'].apply(
                lambda profile_list: ",".join(map(str, profile_list))
            )
            
            # 不要になった一時的な列を削除
            # （もし方位角も保存したい場合は，azimuths_listも同様に文字列化して残す．）
            df = df.drop(columns=['horizon_profile_list', 'azimuths_list'])

            print(f"{csv_path} を保存中...")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print('---')

        print("稜線プロファイルの追記が正常に完了しました．")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
