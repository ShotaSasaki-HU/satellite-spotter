# scripts/add_sqm_value.py

from pathlib import Path
import pandas as pd
import rasterio
import numpy as np
from tqdm import tqdm

# backend/ をPythonの検索パスに追加（先に実行しないとappが見つからないよ．）
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.core.config import get_settings
settings = get_settings()

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "観測候補地点"

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

def main():
    print("SQM値をCSVに追記します．")

    PATH_WORLD_ATLAS_2015_TIFF = settings.PATH_WORLD_ATLAS_2015_TIFF

    try:
        for csv_path in sorted(DATA_DIR.rglob("*.csv")):
            print(f"{csv_path} を処理中...")
            df = pd.read_csv(csv_path, encoding='utf-8', header=0)
            print(f"{len(df)}件のスポットのSQM値を計算中...")

            # tqdmとpandasを連携・プログレスバーの説明を設定
            tqdm.pandas(desc="Calculating SQM Value")

            coords_to_sample = list(zip(df['longitude'], df['latitude']))

            df['sqm_value'] = calc_srm_value(path_world_atlas_2015=PATH_WORLD_ATLAS_2015_TIFF, coords_to_sample=coords_to_sample)

            print(f"{csv_path} を保存中...")
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print('---')

        print("SQM値の追記が正常に完了しました．")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
