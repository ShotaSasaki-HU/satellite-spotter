# src/lambda_worker/s3_utils.py
import os
import boto3
import tempfile
from skyfield.api import load

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
s3 = boto3.client('s3')

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
