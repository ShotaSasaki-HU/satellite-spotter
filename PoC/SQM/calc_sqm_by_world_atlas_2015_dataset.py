# scripts/calc_sqm_by_world_atlas_2015_dataset.py
import rasterio
from pathlib import Path
import numpy as np

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.core.config import get_settings
settings = get_settings()

def calc_srm_value(path_world_atlas_2015: str, coords_to_sample: list[(float, float)]) -> np.ndarray:
    """
    The World Atlas dataset contains calculated artificial brightness in mcd/cm2 (ARTIFICIAL_BRIGHTNESS).
    Assuming that the natural brightness of the night sky is 22.00 mag./arc sec2 or 0.171168465 mcd/m2,
    you can then calculate other properties:

    Total brightness: ARTIFICIAL_BRIGHTNESS + 0.171168465 mcd/m2
    SQM: log10((Total brightness)/108000000)/-0.4
    Ratio: ARTIFICIAL_BRIGHTNESS/0.171168465 mcd/m2
    """
    NATURAL_SKY_BRIGHTNESS_MCD_M2 = 0.171168465
    SQM_CONVERSION_CONSTANT = 108000000
    LOG_BASE_FACTOR = -0.4

    try:
        with rasterio.open(path_world_atlas_2015) as src:
            sample_results = np.array(list(src.sample(coords_to_sample)))
            
            artificial_brightness = sample_results[:, 0]
            artificial_brightness[artificial_brightness < 0] = 0 # 負の値を0にクリップ
            total_brightness = artificial_brightness + NATURAL_SKY_BRIGHTNESS_MCD_M2
            sqm_values = np.log10(total_brightness / SQM_CONVERSION_CONSTANT) / LOG_BASE_FACTOR
        
        return sqm_values

    except rasterio.errors.RasterioIOError:
        print(f"ERROR: World Atlas 2015データセットが見つかりません．: {path_world_atlas_2015}")
        return np.array([])

coords_to_sample = [
    (132.73939, 34.42360), # 20.18 mag/arcsec^2のはず．
    (132.45843, 34.38383), # 18.86
    (132.87457, 34.58993), # 21.76
    (135.49927, 34.77881), # 18.28
    (139.75428, 35.71486), # 17.78
    (143.02029, 43.49114), # 21.94
]

print(calc_srm_value(path_world_atlas_2015=settings.PATH_WORLD_ATLAS_2015_TIFF, coords_to_sample=coords_to_sample))
