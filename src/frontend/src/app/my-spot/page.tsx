// src/app/my-spot/page.tsx
"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { useSearchStore } from "@/store/useSearchStore";
import { useRouter } from "next/navigation";

// SSRを無効化してMapコンポーネントを読み込む
const Map = dynamic(() => import("@/components/Map"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-bg-primary animate-pulse" />,
});

const TOKYO_STATION = { lat: 35.68126494858904, lon: 139.7670650510304 };

export default function MySpotObserverPage() {
  const router = useRouter();
  const { pinPosition, setPinPosition } = useSearchStore(); // Zustandから状態と更新関数を取得
  const [mapCenter, setMapCenter] = useState(TOKYO_STATION); // マップの視点の中心座標
  const [searchQuery, setSearchQuery] = useState(""); // 検索クエリ

  // エンターキーが押された時の検索処理
  const handleSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim() !== "") {
      try {
        // バックエンドのAPIを叩く
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/locations?q=${encodeURIComponent(searchQuery)}&lat=${mapCenter.lat}&lon=${mapCenter.lon}`);
        const data = await res.json();

        if (data.total > 0) {
          // トップの検索結果の座標をピンにセット（これによってMapControllerのflyToが発動する）
          const topResult = data.locations[0];
          setPinPosition({ lat: topResult.lat, lon: topResult.lon });
        } else {
          alert("該当する場所が見つかりませんでした。");
        }
      } catch (error) {
        console.error("エラー：", error);
        alert("検索中にエラーが発生しました。");
      }
    }
  };

  return (
    <div className="relative w-full h-full">
      <Map
        pinPosition={pinPosition}
        setPinPosition={setPinPosition}
        setMapCenter={setMapCenter}
        radius={""}
        step={0}
      />

      <div
        className={`
            absolute top-6 left-0 w-45 md:w-48 h-12
            flex items-center justify-center
            bg-bg-primary border-r-2 border-r-compass-gold z-1000
          `}
      >
        <h1 className="text-compass-gold text-xl md:text-2xl">マイスポット</h1>
      </div>

      {/* 浮いているUIボックス */}
      <div
        className={`
            absolute top-24 left-1/2 -translate-x-1/2
            bg-bg-primary w-[85%] md:w-lg
            border-t-2 border-t-compass-gold z-1000
            p-1
          `}
      >
        {/* ピン立てUI */}
        <div>
          <p className="text-center">あなたが立つ位置にピンを立ててね。</p>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch} // エンターキーの検知
            placeholder="地名や公園名を入力"
            className="block mx-auto my-2 text-text-primary border-compass-gold border rounded-md px-1"
          />
          <div className="flex justify-end">
            <button
              onClick={() => {}}
              className="text-text-primary bg-compass-gold p-2 cursor-pointer"
            >
              次へ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
