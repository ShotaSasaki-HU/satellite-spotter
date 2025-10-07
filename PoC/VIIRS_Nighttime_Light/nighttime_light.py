import rasterio

def query_raster_by_coord(dataset, lat: float, lon: float) -> float:
    return next(dataset.sample([(lon, lat)]))[0]

lat, lon = 35.671144101386936, 139.76926279492196
path_viirs_tiff = "/Volumes/iFile-1/satellite-spotter/VNL_npp_2024_global_vcmslcfg_v2_c202502261200.median_masked.dat.tif"
with rasterio.open(path_viirs_tiff) as viirs_annual:
    stable_light = query_raster_by_coord(viirs_annual, lat, lon)
    print(stable_light)
