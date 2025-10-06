import jismesh.utils as ju

# --- 1. 緯度経度を指定 ---
# 探索したい地点の緯度と経度 (例: 東広島市役所)
latitude = 34.4223
longitude = 132.7441

# --- 2. メッシュコードを計算 ---
# jismesh.to_meshcode(緯度, 経度, メッシュのレベル)
# 1次メッシュ (約80km四方)
primary_mesh = ju.to_meshcode(latitude, longitude, 1)

# 2次メッシュ (約10km四方) - 基盤地図情報のファイル名でよく使われる
secondary_mesh = ju.to_meshcode(latitude, longitude, 2)

# 3次メッシュ (約1km四方)
tertiary_mesh = ju.to_meshcode(latitude, longitude, 3)


print(f"指定した緯度経度: ({latitude}, {longitude})")
print("-" * 30)
print(f"1次メッシュコード: {primary_mesh}")
print(f"2次メッシュコード: {secondary_mesh}")
print(f"3次メッシュコード: {tertiary_mesh}")
print("-" * 30)


# --- 3. ファイル名の構築への応用 ---
# 国土地理院の5mメッシュDEMのファイル名は、多くの場合2次メッシュコードをベースにしている
# 例: FG-GML-5132-37-DEM5A-20161001.xml
# この「5132-37」の部分が2次メッシュコードに相当

# 2次メッシュコードをファイル名で使われる形式に整形
# esh_part_for_filename = f"{secondary_mesh[:4]}-{secondary_mesh[4:]}"

# print(f"この地点が含まれる5mメッシュDEMのファイル名に含まれる可能性のある番号:")
# print(f"-> {mesh_part_for_filename}")
