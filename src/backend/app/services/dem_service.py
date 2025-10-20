# app/services/dem_service.py
import jismesh.utils as ju
import numpy as np
import rasterio
import pyproj
import multiprocessing as mp
from app.core.config import Settings

def get_meshcode_by_coord(lat, lon, n):
    """
    緯度・経度に対応するn次メッシュを返す．
    """
    return ju.to_meshcode(lat, lon, n)

def get_elevations_by_coords(coords: list[dict], settings: Settings) -> np.ndarray:
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

def calc_hidden_height(observer_height: float, target_distance: float) -> float:
    """
    観測者の高さと対象までの距離から，地球の丸みで隠される高さを計算する．

    Args:
        observer_height (float): 観測者の視点の高さ（m）
        target_distance (float): 観測者から対象までの水平距離（m）

    Returns:
        (float): 地球の丸みによって隠される高さ（m）
    """
    EARTH_R = 6371000.0 # 地球の半径（m）

    # 観測者の視点が0m未満の場合，水平線までの距離は0とする．（elseの式に負のobserver_heightが代入できないため．）
    if observer_height < 0:
        dist_to_horizon = 0.0
    else:
        # 観測者の視点から水平線までの距離（厳密式）
        dist_to_horizon = np.sqrt((2 * EARTH_R * observer_height) + (observer_height ** 2))

    if target_distance < dist_to_horizon:
        # 対象が水平線より手前にある場合，地球の丸みによって対象が隠される事は無い．
        return 0.0
    else:
        dist_horizon_to_target = target_distance - dist_to_horizon
        hidden_height = np.sqrt((EARTH_R ** 2) + (dist_horizon_to_target ** 2)) - EARTH_R
        return hidden_height

def calc_viewing_angle(observer_height: float, target_height: float, distance: float) -> float:
    """
    観測者から見た対象の仰角・俯角を計算する．（地球の丸みを考慮）

    Args:
        observer_height (float): 観測者の標高（m）
        target_height (float): 対象となる地形の標高（m）
        distance (float): 観測者から対象までの水平距離（m）

    Returns:
        (float): 仰俯角（度）
    """
    if distance == 0:
        return 90.0 # 真上
    
    hidden_by_curvature = calc_hidden_height(observer_height=observer_height, target_distance=distance) # 地球の丸みによって隠される高さ
    apparent_target_height = target_height - hidden_by_curvature # 観測者から見た，対象の見かけの高さ
    height_diff = apparent_target_height - observer_height
    angle_rad = np.arctan(height_diff / distance) # 近似式（2地点のなす中心角が小さい事を利用）

    return np.degrees(angle_rad)

def calc_max_angle_for_single_azimuth(args):
    """
    1方位分の稜線の最大仰角を計算する．（ワーカープロセスで実行）
    """
    # 引数を展開
    azimuth, observer_lat, observer_lon, observer_height, distances, settings = args

    geod = pyproj.Geod(ellps='WGS84')

    lons, lats, back_azimuth = geod.fwd(
        np.full_like(distances, observer_lon),
        np.full_like(distances, observer_lat),
        np.full_like(distances, azimuth),
        distances
    )

    coords = [{'lat': lat, 'lon': lon} for lat, lon in zip(lats, lons)]
    elevations = get_elevations_by_coords(coords=coords, settings=settings)
    elevations[np.isnan(elevations)] = 0.0

    # 標高値リストの要素それぞれについて仰俯角を計算
    max_angle = -90.0
    for i, dist in enumerate(distances):
        target_height = elevations[i]
        if np.isnan(target_height):
            continue

        current_angle = calc_viewing_angle(
            observer_height=observer_height,
            target_height=target_height,
            distance=dist
        )

        # これまでに見つかった最大仰俯角より大きければ更新
        if current_angle > max_angle:
            max_angle = current_angle

    return max_angle # この方位での最大仰角を返す

def calc_horizon_profile_parallel(
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

    # 各ワーカーに渡す引数（タプル）のリストを作成
    tasks = [(az, observer_lat, observer_lon, observer_height, distances, settings) for az in azimuths]

    # プロセスのプールを作成（CPUコア数を自動で取得）
    # macOSの場合，'fork'だと問題が起きることがあるため'spawn'が推奨されるらしい．
    ctx = mp.get_context('spawn')

    with ctx.Pool(processes=mp.cpu_count()) as pool:
        print(f"{mp.cpu_count()}個のプロセスで並列処理を実行します．")
        # pool.mapを使ってタスクを分配
        horizon_profile = pool.map(calc_max_angle_for_single_azimuth, tasks)

    return np.array(horizon_profile), azimuths
