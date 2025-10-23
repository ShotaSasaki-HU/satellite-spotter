import json
import numpy as np
import skyfield # ...
# from core_logic import calc_horizon_profile, get_events_for_the_coord

# ----------------------------------------------------
# (仮) ここに重い計算ロジックを移植
# ----------------------------------------------------
def calc_my_spot_logic(lat: float, lon: float) -> dict:
    """
    あなたの「マイスポット（7秒）」のロジック。
    （skyfield, numpy, 稜線計算など）
    """
    print(f"計算開始: ({lat}, {lon})")
    # ... 7秒間の重い計算 ...
    # (例: result = calc_horizon_profile(...))
    print("計算完了")

    # 最終的なJSON結果を返す
    return {"message": "MySpot calculation complete", "lat": lat}

def calc_recommendation_logic(lat: float, lon: float) -> dict:
    """
    あなたの「スポット検索（10秒）」のロジック。
    （10地点のスコアリングなど）
    """
    print(f"計算開始: ({lat}, {lon})")
    # ... 10秒間の重い計算 ...
    # (例: result = get_top_spots_by_static_score(...))
    print("計算完了")

    # 最終的なJSON結果を返す
    return {"message": "Recommendation calculation complete", "lat": lat}
# ----------------------------------------------------


def lambda_handler(event, context):
    """
    AWS Lambdaが呼び出すメイン関数

    :param event: FastAPIから渡される入力データ (JSON)
    :param context: 実行コンテキスト (今は無視してOK)
    """
    print(f"受信したイベント: {event}")

    # FastAPIから渡された 'job_type' に応じて処理を分岐
    job_type = event.get('job_type')
    lat = event.get('lat')
    lon = event.get('lon')
    task_id = event.get('task_id') # 👈 ステップ3以降で使います

    try:
        if job_type == 'MY_SPOT':
            result_data = calc_my_spot_logic(lat, lon)
        elif job_type == 'RECOMMENDATION':
            result_data = calc_recommendation_logic(lat, lon)
        else:
            raise ValueError(f"不明なジョブタイプです: {job_type}")

        # ----------------------------------------------------
        # TODO (ステップ3): 結果をDynamoDBに保存する
        # save_to_dynamodb(task_id, "SUCCESS", result_data)
        # ----------------------------------------------------
        print(f"タスク {task_id} 成功")

        return {
            'statusCode': 200,
            'body': json.dumps(result_data)
        }

    except Exception as e:
        # ----------------------------------------------------
        # TODO (ステップ3): エラーをDynamoDBに保存する
        # save_to_dynamodb(task_id, "FAILED", str(e))
        # ----------------------------------------------------
        print(f"タスク {task_id} 失敗: {e}")
        raise e # Lambdaに失敗を通知
