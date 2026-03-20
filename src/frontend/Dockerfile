# ベースイメージとして軽量なNode.js（Alpine Linux）を使用
FROM node:20-alpine

# コンテナ内の作業ディレクトリを /app に設定
WORKDIR /app

# 依存関係のリスト（package.jsonなど）を先にコピーしてインストール
# ソースコードだけを変更した時にインストールの待ち時間をスキップ可能
COPY package*.json ./
RUN npm install

# 残りのソースコードをコピー
COPY . .

# Next.jsのデフォルトポート3000番を開放
EXPOSE 3000

# 開発サーバーを起動
CMD ["npm", "run", "dev"]
