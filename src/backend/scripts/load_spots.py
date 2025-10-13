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

from app.models import Spot

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

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "観測候補地点"

def main():
    print("データベースの登録を開始します．")

    db: Session = SessionLocal()

    try:
        # 既存のデータを全て削除（冪等性を保つため）
        num_deleted = db.query(Spot).delete()
        if num_deleted > 0:
            print(f"{num_deleted}件の既存データを削除しました．")
        
        spots_to_create = []

        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f) # 各行を辞書として読み込み
                for row in reader:
                    geom_wkt = row.get('geometry')
                    if not geom_wkt:
                        continue

                    # WKT (Well-known text)からPOINTかPOLYGONかを判定
                    if geom_wkt.startswith('POINT'):
                        point_geom = geom_wkt
                        polygon_geom = None
                    elif geom_wkt.startswith('POLYGON'):
                        point_geom = f'POINT ({row['latitude']} {row['longitude']})'
                        polygon_geom = geom_wkt
                    else:
                        continue # MULTIPOLYGONなど，POINTでもPOLYGONでもないものはスキップ．
                    
                    spot_data = {
                        'osm_id': int(row.get('id', 0)),
                        'name': row.get('name', 'N/A'),
                        'name_en': row.get('name:en'),
                        'geom': point_geom, # POINTのWKT文字列をセット
                        'polygon_geom': polygon_geom, # POLYGONのWKT文字列またはNoneをセット
                    }
                    spots_to_create.append(spot_data)
        
        # 全てのデータを一括で挿入（バルクインサート）
        print(f"{len(spots_to_create)}件のデータを登録します...")
        db.bulk_insert_mappings(Spot, spots_to_create)

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
