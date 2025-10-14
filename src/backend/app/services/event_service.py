# app/services/event_service.py
from app.schemas.event import Event

def get_events_for_the_coord(
        lat: float,
        lon: float,
        horizon_profile: list[float] | None,
        sky_glow_score: float
    ) -> list[Event] | None:
    """
    単一の座標に対して，観測可能なイベントのリストを取得する．
    """
    # 1. 計算対象にする衛星の国際衛星識別符号を特定
    # 2. 

    return
