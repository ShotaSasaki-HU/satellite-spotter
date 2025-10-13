# scripts/load_locations.py

# このスクリプトを動かす前に：`cd src` -> `docker-compose up -d db`
# 終わったら：`docker-compose down`

import os
import sys
import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.models.location import Location

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
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "大字・町丁目レベル位置参照情報（2024年版)"

def main():
    """
    data/"大字・町丁目レベル位置参照情報（2024年版)" ディレクトリ内の全CSVファイルを再帰的に読み込み，locationsテーブルにデータを登録する．
    """
    print("データベースの登録を開始します．")

    db: Session = SessionLocal()

    try:
        # 既存のデータを全て削除（冪等性を保つため）
        num_deleted = db.query(Location).delete()
        if num_deleted > 0:
            print(f"{num_deleted}件の既存データを削除しました．")
        
        locations_to_create = []

        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            with open(csv_path, mode='r', encoding='cp932') as f: # shift_jisだとエラー
                reader = csv.DictReader(f) # 各行を辞書として読み込み
                for row in reader:
                    # 大字町丁目名がない場合は空文字にする
                    town_name = row.get("大字町丁目名", "")

                    # 検索用のname列を作成
                    full_name = f'{row["都道府県名"]}{row["市区町村名"]}{town_name}'

                    # データベースに登録するオブジェクトの辞書を作成
                    location_data = {
                        'name': full_name,
                        'geom': f"POINT ({row['経度']} {row['緯度']})" # lon -> latの順に注意！
                    }
                    locations_to_create.append(location_data)
        
        # 全てのデータを一括で挿入（バルクインサート）
        print(f"{len(locations_to_create)}件のデータを登録します...")
        db.bulk_insert_mappings(Location, locations_to_create)

        # 変更をコミット
        db.commit()
        print("データ登録が正常に完了しました．")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback() # エラーが発生した場合はロールバック
    finally:
        db.close() # セッションを閉じる

if __name__ == "__main__":
    main()
