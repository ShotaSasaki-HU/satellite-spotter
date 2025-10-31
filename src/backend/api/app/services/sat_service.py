# app/services/sat_service.py
from skyfield.api import load, EarthSatellite, Timescale
from app.core.config import get_settings
import re

class SatDataService:
    """
    TLEデータをロードし，衛星インスタンスをキャッシュするサービス．
    アプリ起動時に一度だけ初期化されることを想定．
    """
    def __init__(self, ts: Timescale):
        print("SatDataService: TLEファイルの読み込みを開始...")

        settings = get_settings()

        starlink_path = settings.get_usable_filepath(file_key=settings.TLE_STARLINK_KEY)
        stations_path = settings.get_usable_filepath(file_key=settings.TLE_STATIONS_KEY)

        starlink_sats = load.tle(starlink_path)
        station_sats = load.tle(stations_path)

        all_sats = list(starlink_sats.values()) + list(station_sats.values())

        # 国際衛星識別番号をキーにした辞書に変換
        self._intldesg_to_sat: dict[str, EarthSatellite] = {}

        for sat in all_sats:
            if sat.model.intldesg:
                self._intldesg_to_sat[sat.model.intldesg] = sat
        
        # 打ち上げグループをキーにした辞書もキャッシュ
        self._launch_group_to_sats: dict[str, list[EarthSatellite]] = {}

        for instance in self._intldesg_to_sat.values():
            intldesg = instance.model.intldesg
            launch_group = re.search(r'\d+', intldesg).group()
            self._launch_group_to_sats.setdefault(launch_group, []) # キーが存在しない時のみ空のリストをセット
            self._launch_group_to_sats[launch_group].append(instance)
        
        print(f"SatDataService: {len(self._intldesg_to_sat)}機の衛星をキャッシュ完了．")
    
        self.ts = ts

    def get_all_satellites(self) -> dict[str, EarthSatellite]:
        """
        キャッシュされた全ての衛星の辞書 {intldesg: instance} を返す．
        """
        return self._intldesg_to_sat
    
    def get_launch_groups(self) -> dict[str, list[EarthSatellite]]:
        """
        キャッシュされた打ち上げグループの辞書 {launch_group: instances} を返す．
        """
        return self._launch_group_to_sats
    
    def get_timescale(self) -> Timescale:
        """
        キャッシュされたTimescaleインスタンスを返す．
        """
        return self.ts

ts = load.timescale()
sat_data_service_instance = SatDataService(ts=ts)

def get_sat_data_service() -> SatDataService:
    """
    FastAPIのDepends()に渡すための関数．
    起動時に作成された単一のインスタンスを返す．
    """
    return sat_data_service_instance
