// src/components/Map.tsx
"use client";

import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect } from "react";

const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// propsの型定義
type MapProps = {
  pinPosition: { lat: number; lon: number };
  setPinPosition: (pos: { lat: number; lon: number }) => void;
  setMapCenter: (pos: { lat: number; lon: number }) => void;
};

// 地図のイベント（クリック等）や視点移動を管理するコンポーネント
function MapController({ pinPosition, setPinPosition, setMapCenter}: MapProps) {
  const map = useMap();

  // クリック（PC）と長押し（スマホのcontextmenu）のイベントを監視
  useMapEvents({
    click(e) {
      setPinPosition({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
    contextmenu(e) {
      setPinPosition({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
    // 地図の移動（ドラッグやズーム）が終わった瞬間に発火するイベント
    moveend(e) {
      const center = e.target.getCenter();
      setMapCenter({ lat: center.lat, lon: center.lng }); // 現在の視点の中心を親に渡す
    },
  });

  // pinPositionが外部（検索など）から変更されたら，その場所に視点を飛ばす．
  useEffect(() => {
    if (pinPosition) {
      // flyTo(座標, ズーム率, オプション)
      map.flyTo([pinPosition.lat, pinPosition.lon], 13, {
        duration: 1.5, // 時間をかけて移動
      });
    }
  }, [pinPosition, map]);

  return <Marker position={[pinPosition.lat, pinPosition.lon]} />;
}

export default function Map({ pinPosition, setPinPosition, setMapCenter }: MapProps) {
  return (
    <MapContainer
      key="satellite-spotter-map" // HMR時のエラー回避のためのキー（効いてない？）
      center={[pinPosition.lat, pinPosition.lon]} // 初期座標
      zoom={14}
      style={{ height: "100%", width: "100%" }} // 親要素いっぱいに広げる
      zoomControl={false} // UIをスッキリさせるために一旦オフ
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapController pinPosition={pinPosition} setPinPosition={setPinPosition} setMapCenter={setMapCenter}/>
    </MapContainer>
  );
}
