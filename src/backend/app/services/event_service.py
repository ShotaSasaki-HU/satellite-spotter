# app/services/event_service.py
from app.schemas.event import Event
import numpy as np
import re
from datetime import datetime

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

def get_potential_trains(sat_instances, circular_std_threshold: float = 1.0):
    # TLEに記載の衛星群を国際衛星識別番号でグルーピング
    launch_groups_with_instances = {} # {グループ名: [衛星インスタンスのリスト]}
    processed_intldesg = set() # 何故か load.tle() において同じ衛星が2重に読まれるため記録

    for name, instance in sat_instances.items():
        intldesg = instance.model.intldesg # 国際衛星識別番号
        if intldesg in processed_intldesg:
            continue
        
        launch_group = re.search(r'\d+', intldesg).group()
        launch_groups_with_instances.setdefault(launch_group, []) # キーが存在しない時のみ空のリストをセット
        launch_groups_with_instances[launch_group].append(instance)

        # 処理が成功したら国際衛星識別番号を記録
        processed_intldesg.add(intldesg)
    
    # トレイン状態にある可能性が高いグループを特定
    launch_groups_in_train_form = {}

    for group_name, instances in launch_groups_with_instances.items():
        # 手動フィルタ
        ng_list = ['21059', '24065'] # スターリンク専用
        if group_name in ng_list:
            continue

        # 打ち上げ年フィルタ

        # TLEの使用は，そもそも1957-2056年に限定されていると推察される．
        # よって，打ち上げ年の上2桁の補完に57年ルールを適用する．
        # https://www.space-track.org/documentation#tle
        launch_year_2_digit = int(group_name[0:2])
        if launch_year_2_digit >= 57:
            launch_year_4_digit = 1900 + launch_year_2_digit
        else:
            launch_year_4_digit = 2000 + launch_year_2_digit
        
        # 今年か去年のみが通過
        current_year = datetime.now().year
        if launch_year_4_digit < (current_year - 1):
            continue

        # グループ内の全衛星から平均近点角（ラジアン）を抽出
        mean_anomalies_rad = [instance.model.mo for instance in instances]
        circular_std = calc_circular_std(mean_anomalies_rad)

        if circular_std < circular_std_threshold:
            launch_groups_in_train_form[group_name] = instances

    return launch_groups_in_train_form

def get_iss_as_a_group_member(sat_instances, iss_intldesgs: list[str] = ['98067A', '21066A']):
    for name, instance in sat_instances.items():
        intldesg = instance.model.intldesg # 国際衛星識別番号
        if intldesg in iss_intldesgs:
            launch_group = re.search(r'\d+', intldesg).group()
            return {launch_group: [instance]}

    return {}

def get_events_for_the_coord(
        location_name: str | None, # スポット以外の場合に渡す事を禁ずる．
        lat: float,
        lon: float,
        horizon_profile: list[float] | None,
        sky_glow_score: float | None,
        starlink_instances, # この関数はルーターから繰り返し呼ばれるため，ファイルI/Oはルーターに任せる．
        station_instances
    ) -> list[Event]:
    """
    単一の座標に対して，観測可能なイベントのリストを取得する．
    """
    # バッチ処理済みのスポットであるにも関わらず，静的スコアが欠損している場合はスキップする．
    if location_name and (not horizon_profile or not sky_glow_score):
        return []
    
    # 計算対象にする衛星の国際衛星識別符号を特定
    target_launch_groups = {}
    target_launch_groups.update(get_potential_trains(sat_instances=starlink_instances))
    target_launch_groups.update(get_iss_as_a_group_member(sat_instances=station_instances))

    # 打ち上げグループごとにイベントを計算

    return
