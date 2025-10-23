# 1. ビルド用ベースイメージに Lambda Python 3.13 を指定（Amazon Linux 2023）
FROM public.ecr.aws/lambda/python:3.13

# 2. 依存ライブラリのインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. 作業ディレクトリを作成 (任意だがあった方が良い)
WORKDIR /var/task

# 4. ローカルのコードをコンテナにコピー
#    (handlerと、もしあれば core_logic.py なども)
COPY lambda_handler.py .
# COPY core_logic.py .

# 5. Lambdaの実行コマンドを設定
#    [ファイル名].[関数名] を指定
CMD [ "lambda_handler.lambda_handler" ]
