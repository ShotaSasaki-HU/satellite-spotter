# src/lambda_worker/rds_utils.py
import os
import psycopg2 # PostgreSQL接続

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

def get_db_connection():
    """
    RDSへの接続情報を取得する．
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER,
            password=DB_PASSWORD, port=5432, connect_timeout=5
        )
        return conn
    except Exception as e:
        print(f"!!! DB接続エラー: {e}")
        raise
