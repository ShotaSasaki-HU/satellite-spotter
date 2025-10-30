# app/core/config.py
from functools import lru_cache
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

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
    DB_HOST: str = 'localhost' # ローカルスクリプト用のデフォルト値
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    AWS_PROFILE: str

    # S3
    S3_BUCKET_NAME: str | None = None
    TLE_STARLINK_KEY: str
    TLE_STATIONS_KEY: str
    DEM_FOLDER_KEY: str
    WORLD_ATLAS_KEY: str

    LOCAL_DATA_ROOT: Path | None = None

    SQM_MIN: float
    SQM_MAX: float
    OPEN_METEO_CONCURRENCY_LIMIT: int

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """
        他のフィールドの値からDATABASE_URLを構築する．
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
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

        if self.S3_BUCKET_NAME:
            return f"s3://{self.S3_BUCKET_NAME}/DEM5A/{first}/{first}-{second}/{first}-{second}-{third}.tif"
        elif self.LOCAL_DATA_ROOT:
            path_dem_tiff = self.LOCAL_DATA_ROOT / f"DEM5A/{first}/{first}-{second}/{first}-{second}-{third}.tif"
            return str(path_dem_tiff) if path_dem_tiff.exists() else None
        else:
            raise ValueError("データソースが設定されていません．")

    # システム環境変数が見つからなかった場合にココを参照
    # Dockerコンテナを起動するときエラーになるため相対パスは設定できない．
    # api/scripts/*.pyを走らせる時は，.envのあるsrc/をカレントディレクトリにすること．
    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = 'utf-8',
        extra='ignore'
    )

@lru_cache
def get_settings() -> Settings:
    """
    Settingsインスタンスを生成し，キャッシュして返す．
    これにより，アプリ全体で単一のSettingsインスタンスが保証される．
    settings = Settings()のグローバルなインスタンスでもシングルトンは実現可能だが，依存性注入DIによる差し替え可能性が無い．
    """
    return Settings()
