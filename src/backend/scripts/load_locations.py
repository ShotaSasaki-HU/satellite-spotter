# scripts/load_locations.py

# このスクリプトを動かす前に：`cd src` -> `docker-compose up -d db`
# 終わったら：`docker-compose down`

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.models.location import Location

# 環境変数の読み込み
from dotenv import load_dotenv
dotenv_path = Path(__file__).resolve().parents[2] / '.env'
print("dotenv_path:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path)

# このスクリプト専用のDB接続情報を生成
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_NAME = os.environ.get("POSTGRES_DB")
LOCAL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"

# このスクリプト専用のDBセッションを確立
engine = create_engine(LOCAL_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "大字・町丁目レベル位置参照情報（2024年版)"

def main():
    """
    data/"大字・町丁目レベル位置参照情報（2024年版)" ディレクトリ内の全CSVファイルを再帰的に読み込み，locationsテーブルにデータを登録する．
    """
    print("データベースの登録を開始します．")

    db: Session = SessionLocal()

    print(DATA_DIR)

if __name__ == "__main__":
    main()
