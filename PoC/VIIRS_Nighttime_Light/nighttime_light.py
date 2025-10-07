import rasterio

def sample_raster_by_coord(dataset, lat: float, lon: float, band: int | None = None):
    """
    ラスターデータから座標に対応する値を取得する．

    Args:
        band: 指定した場合はそのバンドのみ（1始まり）．Noneなら全バンドのnumpy配列を返す．
    """
    values = next(dataset.sample([(lon, lat)]))
    if band is not None:
        return values[band - 1] # rasterioは1始まり
    return values

lat, lon = 35.671144101386936, 139.76926279492196
path_viirs_tiff = "/Volumes/iFile-1/satellite-spotter/VNL_npp_2024_global_vcmslcfg_v2_c202502261200.median_masked.dat.tif"
with rasterio.open(path_viirs_tiff) as viirs_annual:
    stable_light = sample_raster_by_coord(viirs_annual, lat, lon, band=1)
    print(stable_light)
