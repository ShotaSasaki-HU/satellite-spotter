import numpy as np

# 地球の半径（m）
R = 6371000.0

def calc_hidden_height(observer_height: float, target_distance: float) -> float:
    """
    観測者の高さと対象までの距離から，地球の丸みで隠される高さを計算する．

    Args:
        observer_height (float): 観測者の視点の高さ（m）
        target_distance (float): 観測者から対象までの水平距離（m）

    Returns:
        float: 地球の丸みによって隠される高さ（m）
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

h = 10
d = 30000
x = calc_hidden_height(h, d)
print(f"視点の標高{h}mの観測者から見て，距離{d/1000}kmの地点で隠される高さ: {x} m")
