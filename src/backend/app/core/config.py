# app/core/config.py
from functools import lru_cache
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings
from pathlib import Path

# このconfig.pyファイルの絶対パスを取得し，.envファイルのあるsrc/をプロジェクトルートとする．
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = PROJECT_ROOT / '.env'

class Settings(BaseSettings):
    """
    1. Setting()の役割
        ・早期失敗：システム環境変数の不足があれば起動時に停止
        ・型の保証：型変換を一手に担うことでアプリ全体に型安全を提供
        ・バリデーション：環境変数の定義域やフォーマットをチェック．例：Field(default=5, gt=0)，ADMIN_EMAIL: EmailStr
        ・環境変数名の一元管理：システム環境変数の名前を変更する際にコード全体に影響しない．例：Field(alias=...)
    
    2. 読み込み優先順位
        ・コード引数：Settings(port=9999)など
        ・システム環境変数
        ・.envファイル
        ・デフォルト値（クラス宣言内）
    """
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = 'localhost' # ローカルスクリプト用のデフォルト値
    POSTGRES_DB: str

    # データソース設定
    LOCAL_DATA_ROOT: Path | None = None # .envのみに記載
    S3_BUCKET: str | None = None

    # 更新が確実に必要となるファイルは環境変数にして，config.pyの編集を減らす．
    # 今の所，そのようなファイルはなし．

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """
        他のフィールドの値からDATABASE_URLを構築する．
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:5432/{self.POSTGRES_DB}"
    
    @computed_field
    @property
    def PATH_TLE_STARLINK(self) -> str:
        if self.S3_BUCKET:
            return f"s3://{self.S3_BUCKET}/tles/sup-gp_starlink_latest.txt"
        elif self.LOCAL_DATA_ROOT:
            return str(self.LOCAL_DATA_ROOT / "tles" / "sup-gp_starlink_latest.txt")
        else:
            raise ValueError("データソースが設定されていません．")
    
    @computed_field
    @property
    def PATH_TLE_STATIONS(self) -> str:
        if self.S3_BUCKET:
            return f"s3://{self.S3_BUCKET}/tles/stations_latest.txt"
        elif self.LOCAL_DATA_ROOT:
            return str(self.LOCAL_DATA_ROOT / "tles" / "stations_latest.txt")
        else:
            raise ValueError("データソースが設定されていません．")

    @computed_field
    @property
    def PATH_WORLD_ATLAS_2015_TIFF(self) -> str:
        if self.S3_BUCKET:
            return f"s3://{self.S3_BUCKET}/World_Atlas_2015/World_Atlas_2015.tif"
        elif self.LOCAL_DATA_ROOT:
            return str(self.LOCAL_DATA_ROOT / "World_Atlas_2015" / "World_Atlas_2015.tif")
        else:
            raise ValueError("データソースが設定されていません．")
    
    def get_dem_filepath(self, tertiary_meshcode: str) -> str | None:
        """
        3次メッシュコードに対応するTIFFファイルのパスを返す．
        """
        tertiary_meshcode = str(tertiary_meshcode)

        # メッシュコードが8文字であるか確認
        if len(tertiary_meshcode) != 8:
            raise ValueError(f"Invalid tertiary meshcode: {tertiary_meshcode}. It must be 8 digits.")
        
        first = tertiary_meshcode[0:4]
        second = tertiary_meshcode[4:6]
        third = tertiary_meshcode[6:]

        if self.S3_BUCKET:
            return f"s3://{self.S3_BUCKET}/DEM1A/{first}/{first}-{second}/{first}-{second}-{third}.tif"
        elif self.LOCAL_DATA_ROOT:
            path_dsm_tiff = self.LOCAL_DATA_ROOT / f"DEM1A/{first}/{first}-{second}/{first}-{second}-{third}.tif"
            return str(path_dsm_tiff) if path_dsm_tiff.exists() else None
        else:
            raise ValueError("データソースが設定されていません．")

    # システム環境変数が見つからなかった場合にココを参照
    class Config:
        env_file = ENV_FILE_PATH
        env_file_encoding = 'utf-8'

@lru_cache
def get_settings() -> Settings:
    """
    Settingsインスタンスを生成し，キャッシュして返す．
    これにより，アプリ全体で単一のSettingsインスタンスが保証される．
    settings = Settings()のグローバルなインスタンスでもシングルトンは実現可能だが，依存性注入DIによる差し替え可能性が無い．
    """
    return Settings()
