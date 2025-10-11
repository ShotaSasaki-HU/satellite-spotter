import osmnx as ox
import pandas as pd

# Pandasの表示設定（全ての列を表示）
pd.set_option('display.max_columns', None)

# 探索の中心点と範囲を設定
center_point = (34.4223, 132.7442)
search_radius = 15000

# 抽出したい場所のOSMタグを定義
# OSMタグはキーとバリューの組み合わせで場所の種類を定義している．
tags = {
    'leisure': 'park',      # 公園
    'tourism': 'viewpoint', # 展望台
    # 'amenity': 'parking',   # 駐車場
}

# OSMからデータを取得（戻り値はGeoDataFrame）
gdf = ox.features_from_point(center_point, tags, dist=search_radius)
print(f"{len(gdf)}件の候補が見つかりました．")

# name列が存在しない，または名前が空欄のものを除外
# 名前がないものは，大学の駐車場やコンビニだったりする．
candidate_list = gdf[gdf['name'].notna()].copy()

# 緯度経度情報をgeometry列から抽出
candidate_list['latitude'] = candidate_list['geometry'].apply(lambda p: p.centroid.y)
candidate_list['longitude'] = candidate_list['geometry'].apply(lambda p: p.centroid.x)

# 表示する列を絞り込み
candidate_list = candidate_list[['name', 'latitude', 'longitude'] + list(tags.keys())]

print(f"うち，名称が登録されているのは{len(candidate_list)}件です．")

print(candidate_list)
