from skyfield.api import load
import numpy as np
import pandas as pd
from datetime import datetime

def build_name_to_instance_map(path_txt: str) -> dict:
    """衛星名に対するインスタンスの辞書を作成"""
    starlink_all_TLEs = load.tle(path_txt)

    starlink_name_to_instance = {}
    for name, satellite_instance in starlink_all_TLEs.items():
        if 'STARLINK' in str(name):
            starlink_name_to_instance[str(name)] = satellite_instance
    
    return starlink_name_to_instance

def build_group_to_names_map(path_csv):
    """打ち上げグループ名に対する衛星名の辞書を作成"""
    df = pd.read_csv(path_csv, encoding='utf-8', header=0)
    # 国際衛星識別番号から打ち上げグループ名を抽出
    df['LAUNCH_GROUP'] = df['OBJECT_ID'].str.extract(r'(\d{4}-\d{3})')
    # グループ名でグループ化
    return df.groupby('LAUNCH_GROUP')['OBJECT_NAME'].apply(list).to_dict()

def build_group_to_instances(name_to_instance: dict, group_to_names: dict) -> dict:
    """打ち上げグループ名に対するインスタンス群の辞書を作成"""
    launch_groups_with_instances = {} # {グループ名: [衛星インスタンスのリスト]}
    for group, names in group_to_names.items():
        instances = []
        for name in names:
            if name in name_to_instance:
                instances.append(name_to_instance[name])
            else:
                raise ValueError(f"対応するインスタンスが見つかりません．: {name}")
            
        if instances:
            launch_groups_with_instances[group] = instances
    
    return launch_groups_with_instances

def calc_circular_std(rads: list) -> float:
    """
    角度（ラジアン）の配列から円周標準偏差を計算する．

    Args:
        rads (list): 角度（ラジアン）の配列
    Returns:
        (float): 円周標準偏差
    """
    # 角度を単位ベクトルに変換
    x_coords = np.cos(rads)
    y_coords = np.sin(rads)

    # 重心の座標: (c_bar, s_bar)
    c_bar = np.mean(x_coords)
    s_bar = np.mean(y_coords)

    # 平均合成ベクトル長（mean resultant length）: r_bar
    r_bar = np.sqrt(c_bar**2 + s_bar**2)
    # 単位円上の点を平均しているため，0 <= r_bar <= 1．対数を取るためにゼロは回避．
    r_bar = np.clip(r_bar, 1e-12, 1.0)

    # 円周標準偏差
    circular_std_rad = np.sqrt(-2 * np.log(r_bar))
    return circular_std_rad

def find_potential_trains(
        group_to_instances: dict,
        circular_std_threshold: float = 1.0,
        max_age_days: int = 90 # 打ち上げからN日以内のグループのみを対象
    ) -> dict:
    """TLEからトレイン状態にある可能性が高いグループを特定する．"""
    potential_trains = {}

    for group_name, instances in group_to_instances.items():
        # 打ち上げ年フィルタ
        launch_year = int(group_name.split('-')[0])
        current_year = datetime.now().year
        # 今年か去年のみが通過
        if launch_year < (current_year - 1):
            continue

        # グループ内の全衛星から平均近点角（ラジアン）を抽出
        mean_anomalies_rad = [instance.model.mo for instance in instances]
        circular_std = calc_circular_std(mean_anomalies_rad)

        if circular_std < circular_std_threshold:
            potential_trains[group_name] = instances
    
    return potential_trains

if __name__ == "__main__":
    path_sup_gp_txt = "./PoC/Skyfield/sup-gp_starlink_20251008.txt"
    path_sup_gp_csv = "./PoC/Skyfield/sup-gp_starlink_20251008.csv"

    name_to_instance = build_name_to_instance_map(path_txt=path_sup_gp_txt)
    group_to_names = build_group_to_names_map(path_csv=path_sup_gp_csv)
    group_to_instances = build_group_to_instances(name_to_instance=name_to_instance, group_to_names=group_to_names)

    potential_trains = find_potential_trains(group_to_instances=group_to_instances)
    print(f"潜在的なスターリンクトレイン: {list(potential_trains.keys())}")
