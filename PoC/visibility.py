import numpy as np

R = 6371000.0 # 地球の半径（m）

def calc_hidden_height(observer_height: float, target_distance: float) -> float:
    """
    観測者の高さと対象までの距離から，地球の丸みで隠される高さを計算する．

    Args:
        observer_height (float): 観測者の視点の高さ（m）
        target_distance (float): 観測者から対象までの水平距離（m）

    Returns:
        (float): 地球の丸みによって隠される高さ（m）
    """
    # 観測者の視点から水平線までの距離（厳密式）
    dist_to_horizon = np.sqrt((2 * R * observer_height) + (observer_height ** 2))

    if target_distance < dist_to_horizon:
        # 対象が水平線より手前にある場合，地球の丸みによって対象が隠される事は無い．
        return 0.0
    else:
        dist_horizon_to_target = target_distance - dist_to_horizon
        hidden_height = np.sqrt((R ** 2) + (dist_horizon_to_target ** 2)) - R
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
    angle_rad = np.arctan(height_diff / distance)

    return np.degrees(angle_rad)

# --- 使用例 ---
obs_h = 200.0 # 観測者の標高: 200m

# ケース1: 近くの自分より高い山を見る
# 距離5km, 標高1000mの山
angle1 = calc_viewing_angle(obs_h, 1000.0, 5000.0)
print(f"ケース1 (高い山): {angle1:.2f}°")

# ケース2: 遠くの自分より低い丘を見る
# 距離50km, 標高300mの丘（丸みでかなり隠される）
angle2 = calc_viewing_angle(obs_h, 300.0, 50000.0)
print(f"ケース2 (遠い丘): {angle2:.2f}°")

# ケース3: 海を見る
# 距離10km, 標高0mの海面
angle3 = calc_viewing_angle(obs_h, 0.0, 10000.0)
print(f"ケース3 (海): {angle3:.2f}°")

# ケース4: 水平線より遠くにある、かなり高い山を見る
# 距離80km, 標高700mの山
angle4 = calc_viewing_angle(obs_h, 700.0, 80000.0)
print(f"ケース4 (遠方の山): {angle4:.2f}°")
