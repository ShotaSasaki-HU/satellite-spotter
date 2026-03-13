// src/components/Map.tsx
"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
// Leafletのデフォルトアイコンが消えるバグを防ぐためのおまじない
import L from "leaflet";
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl: icon.src,
  shadowUrl: iconShadow.src,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

export default function Map() {
  return (
    <MapContainer
      center={[35.68123458125114, 139.7670535579974]} // 初期座標
      zoom={5}
      style={{ height: "100%", width: "100%" }} // 親要素いっぱいに広げる
      zoomControl={false} // UIをスッキリさせるために一旦オフ
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
    </MapContainer>
  );
}
