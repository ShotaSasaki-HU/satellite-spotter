// src/app/page.tsx
"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { Footprints, Bike, CarFront } from 'lucide-react';
import { useSearchStore } from "@/store/useSearchStore";
import { useRouter } from "next/navigation";

// SSRを無効化してMapコンポーネントを読み込む
const Map = dynamic(() => import("@/components/Map"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-bg-primary animate-pulse" />,
});

const TOKYO_STATION = { lat: 35.68126494858904, lon: 139.7670650510304 };

export default function SpotRecommenderPage() {
  const router = useRouter();
  const { radius, setRadius, pinPosition, setPinPosition } = useSearchStore(); // Zustandから状態と更新関数を取得
  const [step, setStep] = useState<0 | 1>(0); // 0 = ピン立て，1 = 半径入力
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
        radius={radius}
        step={step}
      />

      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <h1 className="text-compass-gold text-xl md:text-2xl">スポット検索</h1>
      </div>

      {/* 浮いているUIボックス */}
      <div
        className={`
          absolute top-22 left-1/2 -translate-x-1/2
          bg-bg-primary w-[90%] md:w-lg
          border border-compass-gold z-1000
          p-2 rounded-xl
        `}
      >
        {/* ステップ1：ピン立てUI */}
        {step === 0 && (
          <div>
            <p className="text-center">１．検索の中心にピンを立ててね。</p>
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
                onClick={() => setStep(1)}
                className="text-text-primary bg-compass-gold p-2 cursor-pointer rounded-lg"
              >
                次へ
              </button>
            </div>
          </div>
        )}

        {/* ステップ2：半径入力UI */}
        {step === 1 && (
          <div>
            <p className="text-center">２．検索半径を入力してね。</p>
            <div className="flex justify-center items-center gap-2 my-2">
              <input
                type="number"
                min={1}
                max={100}
                value={radius}
                onChange={(e) => {
                  const value = e.target.value;
                  setRadius(value === "" ? "" : Number(value));
                }}
                className="w-20 text-text-primary text-center border-compass-gold border rounded-md px-1"
              />
              <span>km</span>
            </div>
            <div className="flex justify-center items-center gap-4 mb-2">
              <Footprints className="w-8 h-8 text-compass-gold hover:text-compass-gold-hover cursor-pointer" onClick={() => setRadius(5)} />
              <Bike className="w-8 h-8 text-compass-gold hover:text-compass-gold-hover cursor-pointer" onClick={() => setRadius(15)}/>
              <CarFront className="w-8 h-8 text-compass-gold hover:text-compass-gold-hover cursor-pointer" onClick={() => setRadius(60)}/>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setStep(0)}
                className="text-text-primary bg-compass-gray p-2 cursor-pointer rounded-lg"
              >
                戻る
              </button>
              <button
                onClick={() => {
                  // 検索条件をクエリパラメータにして結果ページへ遷移
                  router.push(`/results?lat=${pinPosition.lat}&lon=${pinPosition.lon}&radius=${radius}&source=recommender`);
                }}
                className="text-text-primary bg-compass-gold p-2 cursor-pointer rounded-lg"
              >
                検索
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
