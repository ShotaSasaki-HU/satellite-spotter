import jismesh.utils as ju
import os
import rasterio
import numpy as np
import pyproj
import matplotlib.pyplot as plt
import multiprocessing as mp
import timeit

class RasterManager:
    """
    ラスターデータ（GeoTIFF）の効率的な読み込みと，安全なリソース管理を行うためのコンテキストマネージャクラス．

    # 目的
    1. パフォーマンス向上：
       1回の処理（例：稜線計算）の中で同じGeoTIFFファイルを何度も開くのを防ぐ．
       一度開いたファイルはインスタンス内のキャッシュに保持し，ディスクI/Oを最小限に抑える．
    2. 安全なリソース管理：
       with構文と組み合わせることで，処理の正常終了時・異常終了時を問わず，開いた全てのファイルが確実に閉じられることを保証し，メモリリークを防ぐ．
    
    # 使い方
    with RasterManager(path_nighttime_light=...) as rm:
        rm.get_dsm_dataset()などを呼び出す
    # このブロックを抜けた瞬間に、rmが管理していた全てのファイルが自動で閉じられる。
    """
    def __init__(self, path_nighttime_light: str = None):
        self.cache = {} # このインスタンス内だけのキャッシュ
        self.open_datasets = [] # 開いたデータセットを記録
        self.nighttime_light_dataset = None # 夜間光データセット用の属性

        if path_nighttime_light:
            try:
                self.nighttime_light_dataset = rasterio.open(path_nighttime_light)
                self.open_datasets.append(self.nighttime_light_dataset) # 閉じるために記録
            except rasterio.errors.RasterioIOError:
                print(f"ERROR: Nighttime light file not found at {path_nighttime_light}.")
                self.nighttime_light_dataset = None
    
    # with構文が始まった時に呼ばれる
    def __enter__(self):
        return self
    
    # with構文が終わった時に呼ばれる
    def __exit__(self, exc_type, exc_val, exc_tb):
        for dataset in self.open_datasets:
            dataset.close()
    
    def get_dsm_dataset(self, tertiary_meshcode: str):
        # キャッシュを確認
        if tertiary_meshcode in self.cache:
            return self.cache[tertiary_meshcode]
        
        path_dsm_tiff = get_dsm_filepath(tertiary_meshcode)
        if path_dsm_tiff is None:
            return None
        
        dataset = rasterio.open(path_dsm_tiff)
        self.cache[tertiary_meshcode] = dataset
        self.open_datasets.append(dataset) # 閉じるために記録
        return dataset
    
    def get_nighttime_light_dataset(self):
        return self.nighttime_light_dataset # 初期化時に開いた夜間光データセット

def get_meshcode_by_coord(lat, lon, n):
    """
    緯度・経度に対応するn次メッシュを返す．
    ・1次メッシュ：約80km四方
    ・2次メッシュ：約10km四方
    ・3次メッシュ：約1km四方
    """
    return ju.to_meshcode(lat, lon, n)

def get_dsm_filepath(tertiary_meshcode):
    """
    3次メッシュコードに対応するTIFFファイルのパスを返す．
    """
    # メッシュコードが3次メッシュであるか確認
    if len(str(tertiary_meshcode)) != 8:
        raise ValueError(f"Invalid tertiary meshcode: {tertiary_meshcode}. It must be 8 digits.")
    
    tertiary_meshcode = str(tertiary_meshcode)
    first = tertiary_meshcode[0:4]
    second = tertiary_meshcode[4:6]
    third = tertiary_meshcode[6:]
    path_dsm_tiff = f"/Volumes/iFile-1/satellite-spotter/DEM1A/{first}/{first}-{second}/{first}-{second}-{third}.tif"

    if not os.path.exists(path_dsm_tiff):
        return None
    else:
        return path_dsm_tiff

def sample_raster_by_coord(dataset, lat: float, lon: float, band: int | None = None):
    """
    ラスターデータから座標に対応する値を返す．

    Args:
        band: 指定した場合はそのバンドのみ（1始まり）．Noneなら全バンドのnumpy配列を返す．
    """
    # .sample()はジェネレータを返すため，next()で最初の（そして唯一の）結果を取り出す．
    # その結果はNumPy配列なので，[0]で中の数値を取り出す．
    # dataset.sample()には [(経度, 緯度)] の順で座標を渡すことに注意！
    values = next(dataset.sample([(lon, lat)]))
    if band is not None:
        return values[band - 1] # rasterioは1始まり
    return values

def get_elevation_by_coord(lat: float, lon: float, raster_manager: RasterManager) -> float:
    """
    任意の緯度経度に対応するGeoTIFFファイルを見つけて標高値を返す．
    """
    # 緯度経度から3次メッシュコードを計算
    tertiary_meshcode = get_meshcode_by_coord(lat, lon, n=3)
    if not tertiary_meshcode:
        return np.nan
    
    # RasterManager経由で3次メッシュコードに対応するデータセットを取得
    dataset = raster_manager.get_dsm_dataset(tertiary_meshcode)    
    if dataset is None:
        # print(f"DEBUG: DSM file for meshcode {tertiary_meshcode} not found.")
        return np.nan
    
    # 指定した座標の標高値を取得
    try:
        elevation = sample_raster_by_coord(dataset, lat=lat, lon=lon, band=1)
        if elevation < -9000: return np.nan # 一応安全のため
        return elevation
    except IndexError:
        return np.nan

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
    azimuth, observer_lat, observer_lon, observer_height, distances = args

    max_angle = -90.0

    # 各ワーカーは，自分専用のRasterManagerを持つ．
    with RasterManager() as rm:
        geod = pyproj.Geod(ellps='WGS84')

        lons, lats, back_azimuth = geod.fwd(
            np.full_like(distances, observer_lon),
            np.full_like(distances, observer_lat),
            np.full_like(distances, azimuth),
            distances
        )

        for i, dist in enumerate(distances):
            target_lat, target_lon = lats[i], lons[i]
            target_height = get_elevation_by_coord(lat=target_lat, lon=target_lon, raster_manager=rm)
            if np.isnan(target_height):
                continue # 標高データが無ければスキップ

            # 観測者から見た，このサンプリング点の仰俯角を計算
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
        observer_lat: float,
        observer_lon: float,
        observer_eye_height: float = 1.55,
        num_directions: int = 360,
        max_distance: float = 150000.0,
        num_samples: int = 150
    ) -> np.ndarray:
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
    with RasterManager() as rm:
        observer_ground_elev = get_elevation_by_coord(lat=observer_lat, lon=observer_lon, raster_manager=rm)
    if np.isnan(observer_ground_elev):
        raise ValueError("観測地点の標高が取得できませんでした．")
    observer_height = observer_ground_elev + observer_eye_height

    # 計算パラメータの準備
    azimuths = np.linspace(0, 360, num_directions, endpoint=False) # 各方位
    distances = np.geomspace(1, max_distance, num_samples) # 各サンプリング点

    # 各ワーカーに渡す引数（タプル）のリストを作成
    tasks = [(az, observer_lat, observer_lon, observer_height, distances) for az in azimuths]

    # プロセスのプールを作成（CPUコア数を自動で取得）
    # macOSの場合，'fork'だと問題が起きることがあるため'spawn'が推奨されるらしい．
    ctx = mp.get_context('spawn')

    with ctx.Pool(processes=mp.cpu_count()) as pool:
        print(f"{mp.cpu_count()}個のプロセスで並列処理を実行します．")
        # pool.mapを使ってタスクを分配
        horizon_profile = pool.map(calc_max_angle_for_single_azimuth, tasks)
    
    return np.array(horizon_profile), azimuths

def calc_sky_glow_score(
        raster_manager: RasterManager,
        observer_lat: float,
        observer_lon: float,
        search_width: float = 100000.0, # 走査範囲の一辺の長さ（m）
        resolution: float = 500.0 # 格子の解像度（m），VIIRSの解像度は500（m）
    ):
    """
    観測地点を中心とした格子状の領域を走査し，スカイグロウ（光害）のスコアを計算する．
    スコアは各光源の「( 放射輝度 / 距離^2 ) * 面積」の総和となる．
    """
    nighttime_light_dataset = raster_manager.get_nighttime_light_dataset()
    if nighttime_light_dataset is None:
        print("ERROR: Nighttime light dataset not available.")
        return 0.0

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

    sky_glow_score_sum = 0.0 # スカイグロウスコアの合計
    cell_area = resolution ** 2 # 1格子あたりの面積

    # 全ての格子点を走査
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

            # その地点の放射輝度
            radiance = sample_raster_by_coord(
                dataset=nighttime_light_dataset,
                lat=lat,
                lon=lon,
                band=1
            )
            if radiance is None or np.isnan(radiance) or radiance < 0:
                radiance = 0.0
            
            contribution = (radiance / (dist ** 2)) * cell_area
            sky_glow_score_sum += contribution

    return sky_glow_score_sum

# マルチプロセスを使う場合，メインの処理は必ず if __name__ == "__main__": の中に書く．
# 子プロセスが，孫プロセスを生成するのを防ぐため．
if __name__ == "__main__":
    def run_calc():
        lat, lon = 34.259920336746845, 132.68432367066072
    
        horizon_profile, azimuths = calc_horizon_profile_parallel(
            observer_lat=lat,
            observer_lon=lon,
            num_directions=120, # 120 -> 180 とするだけで2秒弱伸びる．
            max_distance=100000, # 50km -> 100km としても実行時間が変わらない．
            num_samples=100 # 100 -> 150 とするだけで2秒弱伸びる．
        )
    
    # 5回実行 × 1セットで計測
    t = timeit.timeit("run_calc()", setup="from __main__ import run_calc", number=5)
    print(f"平均実行時間: {t/5:.3f} 秒")

    """
    plt.figure(figsize=(15,2))
    plt.plot(azimuths, horizon_profile)
    plt.title(f"Horizon Profile at ({lat:.2f}, {lon:.2f})")
    plt.xlabel("Azimuth (degrees from North)")
    plt.ylabel("Elevation Angle (degrees)")
    plt.xticks(np.arange(0, 361, 45), ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'])
    plt.grid(True)
    plt.ylim(min(horizon_profile.min() - 1, -1), horizon_profile.max() + 5) # Y軸の範囲を調整
    plt.show()
    """

    """
    path_viirs_tiff = "/Volumes/iFile-1/satellite-spotter/VNL_npp_2024_global_vcmslcfg_v2_c202502261200.median_masked.dat.tif"

    # with構文を抜けると，RasterManagerが自動で全てのファイルを閉じる．
    with RasterManager(path_nighttime_light=path_viirs_tiff) as rm:
        lat, lon = 35.689432879394246, 139.7005268317204
        print("新宿駅:", calc_sky_glow_score(raster_manager=rm, observer_lat=lat, observer_lon=lon))

        lat, lon = 34.39797522303602, 132.47547768776775
        print("広島駅:", calc_sky_glow_score(raster_manager=rm, observer_lat=lat, observer_lon=lon))

        lat, lon = 34.402651216585774, 132.71277160961336
        print("東広島市:", calc_sky_glow_score(raster_manager=rm, observer_lat=lat, observer_lon=lon))

        lat, lon = 29.246693399224306, 139.18016354401132
        print("太平洋:", calc_sky_glow_score(raster_manager=rm, observer_lat=lat, observer_lon=lon))
    """
