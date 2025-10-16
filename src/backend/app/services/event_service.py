# app/services/event_service.py
from app.schemas.event import Event
from app.core.config import Settings

def get_events_for_the_coord(
        location_name: str | None, # スポット以外の場合に渡す事を禁ずる．
        lat: float,
        lon: float,
        horizon_profile: list[float] | None,
        sky_glow_score: float | None,
        settings: Settings
    ) -> list[Event]:
    """
    単一の座標に対して，観測可能なイベントのリストを取得する．
    """
    # バッチ処理済みのスポットであるにも関わらず，静的スコアが欠損している場合はスキップする．
    if location_name and (not horizon_profile or not sky_glow_score):
        return []
    
    # 計算対象にする衛星の国際衛星識別符号を特定（ISSかスターリンクトレイン）
    target_sats = []

    # 

    return
