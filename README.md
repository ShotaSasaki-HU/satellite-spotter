# Satellite Spotter
人工衛星の観測に最適な場所と時間を推薦するWebアプリケーションです．地形・光害・気象データ等を組み合わせ，ユーザにより良い観測体験を提供します．

## 目次
- [使用技術](#使用技術)
- [主な機能](#主な機能)
- [開発ロードマップ](#開発ロードマップ)

## 使用技術
<p style="display: inline">
    <!-- フロントエンドのフレームワーク一覧 -->
    <!-- バックエンドのフレームワーク一覧 -->
    <!-- バックエンドの言語一覧 -->
    <img src="https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge">
    <img src="https://img.shields.io/badge/-FastAPI-F2C63C.svg?logo=fastapi&style=for-the-badge">
    <!-- ミドルウェア一覧 -->
    <img src="https://img.shields.io/badge/-Postgresql-336791.svg?logo=PostgreSQL&style=for-the-badge">
    <!-- インフラ一覧 -->
    <img src="https://img.shields.io/badge/-Docker-1488C6.svg?logo=docker&style=for-the-badge">
</p>

## 主な機能
- Spot Recommender：指定したエリア周辺から，データに基づいた最適な観測スポットと観測イベントを推薦します．
- My Spot Obeserver：地図上の任意の地点を指定し，データに基づいた最適な観測イベントを推薦します．

## 開発ロードマップ

### 1. テーマ決定
- ブレインストーミング
- アイデア評価（[インパクト対実現可能性マトリクスを見る](idea_selection/impact_feasibility.pdf)）

### 2. 技術実証（Proof of Concept）
アプリケーションのコア機能を実現するため，以下の技術的な検証を行いました．

#### （ア）観測候補地の探索
- 目的：地図データから，夜間の観測に適した「ひらけた場所」や「安全な場所」を抽出する．
- 手法：OpenStreetMapのデータから，候補地点をリストアップするプログラムを実装．
- 成果物：`PoC/osm.py`

#### （イ）衛星通過イベントの予測
- 目的：特定の場所と時間における，人工衛星の可視タイミングと位置を計算する．
- 手法：`Skyfield`ライブラリと最新の軌道データ（TLE）を用いて，人工衛星の位置を算出．また，スターリンクトレイン特有の軌道パターンを検出する独自のアルゴリズムを開発．
- 成果物：`PoC/Skyfield/skyfield_test.py`，`PoC/Skyfield/potential_train.py`

#### （ウ）観測条件のスコアリング
観測候補地の質を定量的に評価するため，複数の地理空間データを用いた指標を作成しました．

- 地形スコア
    - 手法：国土地理院の「基盤地図情報（数値標高モデル）１ｍメッシュ（標高）」を用いて，任意の地点からの可視範囲をシミュレート．計算を高速化するため，Pythonの並列処理を導入．
    - 成果物：`PoC/horizon_profile.py`，`PoC/dem_converter.py`

- 光害スコア
    - 手法（改善前）：~~Suomi-NPP衛星によるVIIRS夜間光画像データを利用し，都市の光が夜空の暗さに与える影響を独自に数値化．~~
    - 手法（改善後）：World Atlas 2015のデータを採用．このデータセットは，VIIRSのデータ等を基にしたモデルによって「地上から見た夜空の明るさ」を計算したものであり，より現実に則した光害の評価が可能．World Atlas 2015の輝度データ（mcd/m²）を，限界等級（NELM）に変換して光害をスコアリング．
    - 成果物：`PoC/VIIRS_Nighttime_Light/sky_glow_score.py`，`PoC/SQM/calc_sqm_by_world_atlas_2015_dataset.py`

- 気象スコア
    - 手法：Open-Meteo APIから取得した気象予報（降水・雲量・視程）を基に，観測当日の空の状態をスコアリング．
    - 成果物：`PoC/open_meteo.py`

- 不快度スコア（未実装）
    - 手法：植生指数や水辺までの距離を使用し，虫が発生するポテンシャルを数値化．
    - 成果物：-

### 3. アプリ設計
- ワイヤーフレームの作成（[ワイヤーフレームを見る](wireframe/wireframe.pdf)）
- OpenAPI仕様書の作成（[仕様書を見る](api_specification/satellite-spotter-api-dev.yml)）

### 4. バックエンドの環境構築
- FastAPIの動作確認
- Dockerイメージのビルド試験
