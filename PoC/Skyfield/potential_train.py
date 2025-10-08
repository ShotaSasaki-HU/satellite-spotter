from skyfield.api import Topos, load
import numpy as np
import pandas as pd
import pprint

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

# 1. 衛星名に対するインスタンスの辞書を作成
path_sup_gp_txt = "./PoC/Skyfield/sup-gp_starlink_20251008.txt"
starlink_all_TLEs = load.tle(path_sup_gp_txt)

starlink_name_to_instance = {}

for name, satellite_instance in starlink_all_TLEs.items():
    if 'STARLINK' in str(name):
        starlink_name_to_instance[str(name)] = satellite_instance

# 2. 打ち上げグループ名に対する衛星名の辞書を作成
path_sup_gp_csv = "./PoC/Skyfield/sup-gp_starlink_20251008.csv"
# path_sup-gp_csv = "https://celestrak.org/NORAD/elements/supplemental/sup-gp.php?FILE=starlink&FORMAT=csv"
df = pd.read_csv(path_sup_gp_csv, encoding='utf-8', header=0)
df['INTERNATIONAL_DESIGNATOR'] = df['OBJECT_ID'].str.extract(r'(\d{4}-\d{3})')

# 3. 打ち上げグループ名に対するインスタンス群の辞書を作成
launch_groups = {} # {グループ名: [衛星インスタンスのリスト]}

for launch_group in df['INTERNATIONAL_DESIGNATOR'].unique():
    df_current_group = df[df['INTERNATIONAL_DESIGNATOR'] == launch_group]
    object_names = df_current_group['OBJECT_NAME'].to_list()

    instances = []

    for name in object_names:
        if name in starlink_name_to_instance:
            instances.append(starlink_name_to_instance[name])
        else:
            raise ValueError(f"対応するインスタンスが見つかりません．: {name}")
    
    launch_groups[launch_group] = instances

pprint.pprint(launch_groups)
