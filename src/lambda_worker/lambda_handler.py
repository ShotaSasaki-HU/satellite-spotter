# src/lambda_worker/lambda_handler.py
import os
import psycopg2 # PostgreSQL接続
import boto3 # S3接続
from skyfield.api import load
import json
import tempfile

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
s3 = boto3.client('s3')

DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

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

def load_tle_from_s3(file_key: str):
    """
    AWS S3からTLEファイルをLambdaの/tmpにダウンロードし，skyfieldで読み込む．
    skyfield.api.load.tle() がファイルパス文字列を強く期待するため，一度ダウンロードする．
    """
    local_temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(file_key))

    try:
        print(f"S3ファイルを一時パスにダウンロード中: {S3_BUCKET_NAME}/{file_key} -> {local_temp_path}")
        s3.download_file(Bucket=S3_BUCKET_NAME, Key=file_key, Filename=local_temp_path)
        print("ダウンロード完了．")

        satellites = load.tle(local_temp_path)
        print(f"TLE読み込み完了．{len(satellites)}個の衛星インスタンスをロード．")

        return satellites
    except Exception as e:
        print(f"!!! S3からのTLE読み込みエラー: {e}")
        raise

def lambda_handler(event, context):
    """
    RDSとS3の接続テスト用ハンドラ
    """
    print(f"受信したイベント: {event}")

    # テスト用のパラメータを引数から取得
    test_db_query = event.get('test_db_query', None)
    test_s3_file_key = event.get('test_s3_file_key', None)

    results = {}
    errors = {}

    # RDS接続テスト
    conn = None # finallyで閉じるために外で宣言
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print(f"RDSテストクエリ実行: {test_db_query}")
        cur.execute(test_db_query)
        db_result = cur.fetchone()
        print(f"RDSクエリ結果: {db_result}")
        results['db_test'] = f"Query OK, result: {db_result}"
        cur.close()
    except Exception as e:
        print(f"!!! RDSテスト中にエラー: {e}")
        errors['db_test'] = f"Failed: {e}"
    finally:
        if conn:
            conn.close()
            print("DB接続を閉鎖．")

    # S3接続テスト
    try:
        satellites = load_tle_from_s3(test_s3_file_key)
        results['s3_test'] = f"Load OK, loaded {len(satellites)} satellites."
    except Exception as e:
        print(f"!!! S3テスト中にエラー: {e}")
        errors['s3_test'] = f"Failed: {e}"

    # --- 結果を返す ---
    if errors:
        print(f"テスト中にエラーが発生しました: {errors}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'テスト中にエラーが発生しました．',
                'errors': errors,
                'successes': results
            })
        }
    else:
        print("RDSとS3の接続テスト成功！")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'RDSとS3の接続テスト成功！',
                'results': results
            })
        }

"""
{
    "test_db_query": "SELECT COUNT(*) FROM spots;",
    "test_s3_file_key": "tles/stations_latest.txt"
}
"""
