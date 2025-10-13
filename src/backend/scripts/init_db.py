# scripts/inti_db.py

# このスクリプトを動かす前に：`cd src` -> `docker-compose up -d db`
# 終わったら：`docker-compose down`

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
sys.path.append(str(Path(__file__).resolve().parent.parent))

# base.pyをインポートすることで、Baseを継承した全てのモデルがSQLAlchemyに認識される
from app.db import base

# 環境変数の読み込み
dotenv_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=dotenv_path)

# このスクリプト専用のDB接続情報を生成
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_NAME = os.environ.get("POSTGRES_DB")
LOCAL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"

# このスクリプト専用のDBセッションを確立
engine = create_engine(LOCAL_DATABASE_URL)

print("データベースのテーブルを作成します...")

# Baseに紐づけられた全てのテーブルをデータベース内に作成する
base.Base.metadata.create_all(bind=engine)

print("テーブルの作成が完了しました。")
