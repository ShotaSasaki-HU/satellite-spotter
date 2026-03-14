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

      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <h1 className="text-compass-gold text-xl md:text-2xl">マイスポット</h1>
      </div>
    </div>
  );
}
