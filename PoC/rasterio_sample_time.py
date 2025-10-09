import rasterio
import timeit
import random

path = "/Volumes/iFile-1/satellite-spotter/DEM1A/5132/5132-55/5132-55-09.tif"
dataset = rasterio.open(path)

lat, lon = 34.4223, 132.7441

coords = []
for _ in range(10000):
    coords.append((lat + (random.random() / 100), lon + (random.random() / 100)))

def sample_1coord_100times():
    for coord in coords:
        values = next(dataset.sample([coord]))[0]

def sample_100coord_once():
    values = next(dataset.sample(coords))[0]

N = 10

t = timeit.timeit("sample_1coord_100times()", number=N, globals=globals())
print(f"平均実行時間: {t/N} 秒")
# 平均実行時間: 0.11723239170023589 秒

t = timeit.timeit("sample_100coord_once()", number=N, globals=globals())
print(f"平均実行時間: {t/N} 秒")
# 平均実行時間: 3.340420007589273e-05 秒
