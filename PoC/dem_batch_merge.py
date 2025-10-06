import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.merge import merge

# ---------- 入力フォルダ ----------
input_folder = "/Volumes/iFile-1/5132"

# ---------- 名前空間 ----------
ns = {
    'gml': 'http://www.opengis.net/gml/3.2',
    'fgd': 'http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema'
}

# ---------- 個別XML処理 ----------
def process_xml_to_tif(input_xml):
    print(f"▶ 処理中: {input_xml}")
    output_tif = os.path.splitext(input_xml)[0] + ".tif"

    tree = ET.parse(input_xml)
    root = tree.getroot()

    lower = root.find(".//gml:lowerCorner", ns).text.strip().split()
    upper = root.find(".//gml:upperCorner", ns).text.strip().split()
    lat_min, lon_min = map(float, lower)
    lat_max, lon_max = map(float, upper)

    high = root.find(".//gml:high", ns).text.strip().split()
    width = int(high[0]) + 1
    height = int(high[1]) + 1

    tuple_list = root.find(".//gml:tupleList", ns).text.strip().splitlines()
    values = []
    for line in tuple_list:
        if "," not in line:
            print("カンマがない事がある！")
            continue
        label, val = line.strip().split(",")
        if val == "-9999.":
            values.append(np.nan)
        else:
            values.append(float(val))

    arr = np.array(values).reshape((height, width))

    pixel_size_x = (lon_max - lon_min) / width
    pixel_size_y = (lat_max - lat_min) / height
    transform = from_origin(lon_min, lat_max, pixel_size_x, pixel_size_y)

    with rasterio.open(
        output_tif, "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:6668",
        transform=transform,
        nodata=np.nan
    ) as dst:
        dst.write(arr.astype("float32"), 1)

    print(f"✅ 完了: {output_tif}")
    return output_tif

# ---------- 全体の処理 ----------
xml_files = glob.glob(os.path.join(input_folder, "*.xml"))
tif_files = []

if not xml_files:
    print("⚠ 対象のXMLファイルが見つかりません")
else:
    # 1. GeoTIFF作成
    for xml_file in xml_files:
        try:
            tif_path = process_xml_to_tif(xml_file)
            tif_files.append(tif_path)
        except Exception as e:
            print(f"❌ エラー: {xml_file} → {e}")

    """
    # 2. GeoTIFFを合成
    if tif_files:
        print("🧵 GeoTIFFモザイク処理中...")
        src_files_to_mosaic = [rasterio.open(fp) for fp in tif_files]
        mosaic, out_trans = merge(src_files_to_mosaic)

        out_meta = src_files_to_mosaic[0].meta.copy()
        out_meta.update({
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "nodata": np.nan
        })

        with rasterio.open("merged_output.tif", "w", **out_meta) as dest:
            dest.write(mosaic)

        print("✅ モザイクGeoTIFF出力完了: merged_output.tif")
    """
