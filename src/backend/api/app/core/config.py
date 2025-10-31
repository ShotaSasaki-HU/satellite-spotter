# app/core/config.py
from functools import lru_cache
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import boto3
import tempfile
import os

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
    DB_PORT: int = 5432
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
    
    @property
    def s3_client(self):
        """
        S3クライアントを初期化して返す．
        """
        return boto3.client('s3')
    
    def get_usable_filepath(self, file_key: str) -> str:
        """
        S3またはローカルのデータにアクセスするためのファイルパスを返す．
        S3の場合は，/tmpにダウンロードする．
        """
        if self.S3_BUCKET_NAME:
            bucket = self.S3_BUCKET_NAME
            local_path = os.path.join(tempfile.gettempdir(), file_key) # 例: /tmp/tles/sup-gp_starlink_latest.txt
            local_dir = os.path.dirname(local_path) # 例: /tmp/tles

            if not os.path.exists(local_path):
                os.makedirs(local_dir, exist_ok=True) # 親ディレクトリが存在しなければ再帰的に作成

                try:
                    print(f"S3: Downloading s3://{bucket}/{file_key} -> {local_path}")
                    self.s3_client.download_file(bucket, file_key, local_path)
                    print("S3: Download complete.")
                except Exception as e:
                    print(f"!!! S3 download error: {e}")
                    raise FileNotFoundError(f"S3 object not found or error: s3://{bucket}/{file_key}")
            
            return local_path
        
        elif self.LOCAL_DATA_ROOT:
            local_path = self.LOCAL_DATA_ROOT / file_key
            print(f"Local: Accessing {local_path}")
            if not local_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_path}")
            return str(local_path)
        
        else:
            raise ValueError("データソースが設定されていません (S3_BUCKET_NAME も LOCAL_DATA_ROOT も未設定)")
    
    def get_dem_filepath(self, tertiary_meshcode: str) -> str | None:
        """
        3次メッシュコードに対応するTIFFファイルのパスを返す．
        """
        # メッシュコードが8文字であるか確認
        tertiary_meshcode = str(tertiary_meshcode)
        if len(tertiary_meshcode) != 8:
            raise ValueError(f"Invalid tertiary meshcode: {tertiary_meshcode}. It must be 8 digits.")
        
        first = tertiary_meshcode[0:4]
        second = tertiary_meshcode[4:6]
        third = tertiary_meshcode[6:]

        # S3キーまたはローカルのサブパスを構築
        file_key = f"{self.DEM_FOLDER_KEY}/{first}/{first}-{second}/{first}-{second}-{third}.tif"
        
        try:
            return self.get_usable_filepath(file_key) # 汎用ヘルパーを呼び出す
        except FileNotFoundError:
            # DEMファイルが存在しないのはエラーではないため None を返す．
            return None
        except Exception as e:
            print(f"!!! get_dem_filepath error: {e}")
            raise

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
