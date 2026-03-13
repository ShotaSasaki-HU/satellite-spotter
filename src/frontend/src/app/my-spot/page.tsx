// src/app/my-spot/page.tsx
"use client";

import dynamic from "next/dynamic";

// SSRを無効化してMapコンポーネントを読み込む
const Map = dynamic(() => import("@/components/Map"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-bg-primary animate-pulse" />,
});

export default function MySpotObserverPage() {
  return (
    <div className="relative w-full h-full">
      {/* 地図コンポーネント */}
      <Map />

      <div className="absolute top-4 left-4 z-1000">
        <h1 className="text-2xl font-bold">マイスポット</h1>
      </div>
    </div>
  );
}
