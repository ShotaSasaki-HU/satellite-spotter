from skyfield.api import Topos, load
import requests
from datetime import timedelta, timezone

########## ISSココカラ ##########

ts = load.timescale()
t0 = ts.now()

osaka = Topos('34.6914 N', '135.4917 E')

satellites = load.tle('http://celestrak.com/NORAD/elements/stations.txt')
iss = satellites['ISS (ZARYA)']

alt, az, distance = (iss - osaka).at(t0).altaz()

print('高度:{0:.1f} 度'.format(alt.degrees))
print('方位角:{0:.1f} 度'.format(az.degrees))
print('距離:{0:.0f} km'.format(distance.km))

########## ISSココマデ ##########

########## Starlink群をインスタンス化ココカラ ##########

ts = load.timescale()
t0 = ts.now()

osaka = Topos('34.6914 N', '135.4917 E')

# starlink_all_TLEs = load.tle('https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle')

sup_gp_url = 'https://celestrak.org/NORAD/elements/supplemental/sup-gp.php?FILE=starlink&FORMAT=tle'
response = requests.get(sup_gp_url)

with open("starlink.txt", "w") as f:
    f.write(response.text)

starlink_all_TLEs = load.tle('starlink.txt')

# Starlink衛星
starlink_instances = []

for name, satellite_instance in starlink_all_TLEs.items():
    if 'STARLINK' in str(name):
        starlink_instances.append(satellite_instance)

print(f"取得したStarlink衛星の数: {len(starlink_instances)}機")

for instance in starlink_instances[-1:]:
    alt, az, distance = (instance - osaka).at(t0).altaz()
    print(f"{instance.name}: 高度: {alt.degrees:.1f} 度, 方位角: {az.degrees:.1f} 度, 距離: {distance.km} km")

########## Starlink群をインスタンス化ココマデ ##########

########## 天球内のパスを発見するメソッドココカラ ##########
"""
find_eventsメソッドを使えば，指定期間内にインスタンスが任意地点上空を通るパスのうち，指定仰角以上となる全てのパスの（出現時刻・最大仰角となる時刻・没時刻）を一度に得ることができる．
"""

ts = load.timescale()
t0 = ts.now()
t1 = ts.utc(t0.utc_datetime() + timedelta(days=1))
tz = timezone(timedelta(hours=9))

t, events = starlink_instances[0].find_events(osaka, t0, t1, altitude_degrees=10.0)

for ti, event in zip(t, events):
    if event == 0:
        print('見え始め', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
    if event == 1:
        print('最大仰角', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
    if event == 2:
        print('見え終わり', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
        print()

########## 天球内のパスを発見するメソッドココマデ ##########

########## 太陽と可視タイミングの関係ココカラ ##########

eph = load('de421.bsp')
sun, earth = eph['sun'], eph['earth']

ts = load.timescale()
t0 = ts.now()
t1 = ts.utc(t0.utc_datetime() + timedelta(days=1))
tz = timezone(timedelta(hours=9))

t, events = starlink_instances[0].find_events(osaka, t0, t1, altitude_degrees=10.0)

sun_alt = (earth + osaka).at(t).observe(sun).apparent().altaz()[0].degrees
sun_lit = starlink_instances[-1].at(t).is_sunlit(eph)

for ti, event, s_alt, s_lit in zip(t, events, sun_alt, sun_lit):
    if s_alt < -6 and s_lit == True:
        if event == 0:
            print('見え始め', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
        if event == 1:
            print('最大仰角', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
        if event == 2:
            print('見え終わり', ti.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'), 'JST')
            print()

########## 太陽と可視タイミングの関係ココマデ ##########
