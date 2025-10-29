# src/lambda_worker/lambda_handler.py
import json
import traceback
from rds_utils import get_db_connection
from s3_utils import load_tle_from_s3
from dynamodb_utils import table

def lambda_handler(event, context):
    """
    DynamoDB書き込みテストを含むRDSとS3の接続テスト用ハンドラ
    """
    print(f"受信したイベント: {event}")

    # テスト用のパラメータを引数から取得
    test_db_query = event.get('test_db_query', None)
    test_s3_file_key = event.get('test_s3_file_key', None)

    job_type = event.get('job_type', None)
    task_id = event.get('task_id', None)

    if not task_id:
        # FastAPIがtask_idを生成して渡すのが必須
        error_message = "task_idがイベントに含まれていません．"
        print(f"エラー: {error_message}")
        return {'statusCode': 400, 'body': json.dumps({'error': error_message})}

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
    
    # DynamoDB書き込みテスト
    try:
        # 本番では，FastAPIが先にPENDINGを書き込んでいる．
        print(f"タスク {task_id}: ステータスを RUNNING に更新中...")
        # update_itemは項目が存在しない場合，自動的に新規作成する．
        table.update_item(
            Key={'task_id': task_id},
            UpdateExpression="SET job_status = :status, start_time_ms = :start",
            ExpressionAttributeValues={
                ':status': 'RUNNING',
                ':start': context.get_remaining_time_in_millis() # 開始時の残り時間 (参考)
            }
        )
        print(f"タスク {task_id}: ステータス更新完了 (RUNNING)")

        result_data = {"message": "Calculation finished after 10.0 seconds."}

        print(f"タスク {task_id}: 結果をDynamoDBに保存中...")
        table.update_item(
            Key={'task_id': task_id},
            UpdateExpression="SET job_status = :status, result_data = :res, end_time_ms = :end",
            ExpressionAttributeValues={
                ':status': 'SUCCESS',
                ':res': json.dumps(result_data), # 結果はJSON文字列
                ':end': context.get_remaining_time_in_millis()
            }
        )
        print(f"タスク {task_id}: 保存完了 (SUCCESS)")
    
    except Exception as e:
        # --- エラー処理 ---
        error_message = str(e)
        error_traceback = traceback.format_exc()
        print(f"!!! タスク {task_id}: エラー発生 !!!\n{error_traceback}")

        # --- DynamoDB: 失敗時にステータスとエラー情報を保存 ---
        print(f"タスク {task_id}: エラー情報をDynamoDBに保存中...")
        try:
            table.update_item(
                Key={'task_id': task_id},
                UpdateExpression="SET job_status = :status, error_message = :err, error_traceback = :tb, end_time_ms = :end",
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':err': error_message,
                    ':tb': error_traceback,
                    ':end': context.get_remaining_time_in_millis()
                }
            )
            print(f"タスク {task_id}: エラー情報保存完了 (FAILED)")
        except Exception as db_error:
            print(f"★★★ DynamoDBへのエラー書き込みに失敗しました: {db_error}")
        # ----------------------------------------------------

        print(f"!!! DynamoDBテスト中にエラー: {e}")
        errors['dynamodb_test'] = f"Failed: {e}"

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
        print("RDS・S3・DynamoDBの接続テスト成功！")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'RDS・S3・DynamoDBの接続テスト成功！',
                'results': results
            })
        }

"""
{
    "task_id": "dynamodb-test-001",
    "job_type": "TEST",
    "test_db_query": "SELECT COUNT(*) FROM spots;",
    "test_s3_file_key": "tles/stations_latest.txt"
}
"""
