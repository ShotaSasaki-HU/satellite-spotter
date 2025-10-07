import io
import numpy as np
import xml.etree.ElementTree as ET
import rasterio
from rasterio.transform import from_origin
import glob
import os
import gc
from tqdm import tqdm

class xmlDem:
    def __init__(self) -> None:
        self.ns = {
        'gml': 'http://www.opengis.net/gml/3.2',
        'fgd': 'http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema'
        }

    def read_xml(self,file_path:str|bytes) -> None:

        if isinstance(file_path, str):
            # ファイルパスなら普通に読む
            tree = ET.parse(file_path)
        elif isinstance(file_path, bytes):
            # bytesならBytesIOで読む
            tree = ET.parse(io.BytesIO(file_path))
        else:
            raise ValueError(f"Unsupported file type: {type(file_path)}")

        self.root = tree.getroot()
        self.type = self.root.find('.//fgd:type', namespaces=self.ns).text
        self.meshcode = self.root.find('.//fgd:mesh', namespaces=self.ns).text
        self.envelope = self.root.find('.//gml:Envelope', namespaces=self.ns)        

        self.tupleList = self.root.find('.//gml:tupleList', self.ns).text
        self.lowerCorner = self.root.find('.//gml:lowerCorner', self.ns).text
        self.upperCorner = self.root.find('.//gml:upperCorner', self.ns).text
        self.GridEnvelope = self.root.find('.//gml:GridEnvelope', self.ns)
        self.low = self.GridEnvelope.find('gml:low', self.ns).text
        self.high = self.GridEnvelope.find('gml:high', self.ns).text
        self.startPoint = self.root.find('.//gml:startPoint', self.ns).text
        self.sequenceRule = self.root.find('.//gml:sequenceRule', self.ns).attrib.get('order')

        self._gridinfo()
        self._setcrs()
    def _setcrs(self):
        assert self.envelope is not None 
        srs_name = self.envelope.attrib.get('srsName')
        if srs_name == "fguuid:jgd2011.bl":
            self.epsg = '6668'
        elif srs_name == "fguuid:jgd2024.bl":
            self.epsg = '6668'
        else:
            print(f"Unknown SRS Name:{srs_name}")

    def _gridinfo(self):
        self.nlon = int(self.high.split()[0]) - int(self.low.split()[0]) + 1
        self.nlat = int(self.high.split()[1]) - int(self.low.split()[1]) + 1
        self.llat, self.llon = np.array(self.lowerCorner.split(),dtype=float)
        self.ulat, self.ulon = np.array(self.upperCorner.split(),dtype=float)
        
        self.dlon = (self.ulon - self.llon) / self.nlon
        self.dlat = (self.ulat - self.llat) / self.nlat
        
        self.lat0 = self.ulat #左上座標の緯度
        self.lon0 = self.llon #左上座標の経度

        self.lonc = [self.lon0 + 0.5*self.dlon + self.dlon*_ for _ in range(self.nlon)]
        self.latc = [self.lat0 - 0.5*self.dlat - self.dlat*_ for _ in range(self.nlat)]

        self.lon_array = np.array(self.lonc)
        self.lat_array = np.array(self.latc)
        

        if self.sequenceRule is not None and self.startPoint is not None:
            order = self.sequenceRule
            start_x, start_y = map(int, self.startPoint.split())
        else:
            order = "+x-y"
            start_x, start_y = 0, 0  # デフォルト仮定
            print("[Warning] <sequenceRule> または <startPoint> が見つかりませんでした。")
            print("          デフォルト値 order='+x-y', startPoint=(0,0) を仮定して処理します。")

        self.Z = np.full((self.nlat, self.nlon), np.nan, dtype=float)

        _desc =  np.array([_.split(",")[0] for _ in self.tupleList.split()])
        _value = np.array([float(_.split(",")[1]) for _ in self.tupleList.split()])
        _value = np.where(_value == -9999, np.nan, _value)

        if order == "+x-y":
            # フラットなインデックス計算
            flat_start_idx = start_y * self.nlon + start_x

            # 1D化して挿入
            Z_flat = self.Z.flatten()
            Z_flat[flat_start_idx:flat_start_idx + len(_value)] = _value

            # 2Dに戻す
            self.Z = Z_flat.reshape((self.nlat, self.nlon))
        else:
            raise NotImplementedError(f"Order '{order}' not supported yet.")

        self.LON, self.LAT = np.meshgrid(self.lon_array, self.lat_array)

    def info(self):
        print(f"type     = {self.type}")
        print(f"meshcode = {self.meshcode}")
        print(f"nlon     = {self.nlon}")
        print(f"nlat     = {self.nlat}")

    def to_geotiff(self, output_path: str):
        """
        標高データをGeoTIFFで保存する
        """
        # ピクセルサイズ
        pixel_width = abs(self.dlon)
        pixel_height = abs(self.dlat)

        # 左上の座標（原点）
        west = self.llon
        north = self.ulat

        # アフィン変換（位置とピクセル解像度をセット）
        transform = from_origin(west, north, pixel_width, pixel_height)

        # GeoTIFFとして保存
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=self.Z.shape[0],
            width=self.Z.shape[1],
            count=1,
            dtype=self.Z.dtype,
            crs=f"EPSG:{self.epsg}",
            transform=transform,
        ) as dst:
            dst.write(self.Z, 1)

        print(f"Saved GeoTIFF: {output_path}")

target = "/Users/shotasasaki/Downloads/target"
input_folders = [
    f for f in os.listdir(target) if os.path.isdir(os.path.join(target, f))
]

for input_folder in tqdm(input_folders):
    xml_files = glob.glob(os.path.join(*[target, input_folder, "*.xml"]))

    if not xml_files:
        print("対象のXMLファイルが見つかりません．")
    else:
        for xml_file in xml_files:
            # print(f"▶ 処理中: {xml_file}")

            dem = xmlDem()
            dem.read_xml(file_path=xml_file)

            primary = str(os.path.splitext(xml_file)[0][-25:-21])
            secondary = str(os.path.splitext(xml_file)[0][-20:-18])
            # tertiary = str(os.path.splitext(xml_file)[0][-17:-15])

            dir_path = f"/Volumes/iFile-1/satellite-spotter/DEM1A/{primary}/{primary}-{secondary}"
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)

            output_name = f"{dir_path}/{os.path.splitext(xml_file)[0][-32:]}.tif"
            dem.to_geotiff(output_name)

            del dem
            gc.collect() # 強制的にメモリを回収

print("✅")
