// src/app/detail/page.tsx
"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { TrajectoryResponse } from "@/types/trajectory";
import { Loader2, ChevronLeft, Play, Pause } from "lucide-react";
import { useRouter } from "next/navigation";

import dynamic from "next/dynamic";
const SkySimulator = dynamic(() => import("@/components/SkySimulator"), {
  ssr: false, // サーバー側での描画を絶対にさせない
  loading: () => (
    <div className="h-full w-full flex flex-col items-center justify-center bg-black">
      <Loader2 className="animate-spin text-compass-gold mb-4" size={40} />
      <p className="text-compass-gold tracking-widest text-sm animate-pulse">
        宇宙空間を生成中...
      </p>
    </div>
  ),
});

function DetailContent() {
  const router = useRouter();

  const searchParams = useSearchParams();
  const locationName = searchParams.get("location_name") || "観測スポット";
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const startTime = searchParams.get("start_time");
  const endTime = searchParams.get("end_time");
  // クエリパラメータから配列を受け取るハック（URLSearchParams.getAll）
  const designators = searchParams.getAll("intldesg"); 

  const [data, setData] = useState<TrajectoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // スライダーのインデックス
  const [timeIndex, setTimeIndex] = useState(0);

  useEffect(() => {
    if (!lat || !lon || !startTime || !endTime || designators.length === 0) return;

    const fetchTrajectory = async () => {
      try {
        // クエリ配列の構築 (?intldesg=A&intldesg=B...)
        const desgQuery = designators.map(d => `international_designators=${encodeURIComponent(d)}`).join("&");
        const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/trajectories?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}&lat=${lat}&lon=${lon}&${desgQuery}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("軌道データの取得に失敗しました");
        
        const result: TrajectoryResponse = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrajectory();
  }, [lat, lon, startTime, endTime]);

  if (loading) return <div className="h-full w-full flex justify-center items-center"><Loader2 className="animate-spin text-compass-gold" size={48} /></div>;
  if (error) return <div className="text-red-500 text-center mt-20">{error}</div>;
  if (!data || data.trajectories.length === 0) return <div>データがありません</div>;

  // 現在のインデックスに対応するデータ
  const currentTrajectory = data.trajectories[timeIndex];
  // 時刻を日本時間で見やすくフォーマット
  const currentTimeStr = new Date(currentTrajectory.timestamp).toLocaleTimeString("ja-JP", {
    timeZone: "Asia/Tokyo",
    month: "short", day: "numeric", weekday: "short",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });

  return (
    <div className="relative w-full h-full bg-black">
      {/* 3D天球キャンバス（全画面） */}
      <div className="absolute inset-0 z-0">
        <SkySimulator currentPositions={currentTrajectory.positions} />
      </div>

      {/* ヘッダーUI（前面） */}
      <div className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <div className="w-full flex justify-center items-center gap-3">
          {/* ブラウザバック */}
          <button onClick={() => router.back()}>
            <ChevronLeft size={30} className="text-compass-gray hover:text-compass-gray-hover"/>
          </button>
          <h1 className="text-compass-gold text-xl md:text-2xl">見えかた</h1>
        </div>
      </div>

      {/* 下部のスライダーUI */}
      <div className={`
          absolute bottom-3 left-1/2 -translate-x-1/2 w-[90%] md:w-[500px]
          bg-bg-primary border border-compass-gold/70 rounded-xl p-4 z-10
        `}
      >
        <div className="flex flex-col md:flex-row md:gap-6 justify-between items-center mb-2">
          <span className="text-compass-gold text-xl tracking-wider shrink-0">{currentTimeStr}</span>
          <span className="text-text-muted text-base truncate">{locationName}</span>
        </div>
        
        {/* レンジスライダー */}
        <input
          type="range"
          min={0}
          max={data.trajectories.length - 1}
          value={timeIndex}
          onChange={(e) => setTimeIndex(Number(e.target.value))}
          className="w-full accent-compass-gold cursor-pointer"
        />
        
        <div className="flex justify-between text-xs text-text-muted mt-1">
          <span>見え始め</span>
          <span>見え終わり</span>
        </div>
      </div>
    </div>
  );
}

export default function DetailPage() {
  return (
    <Suspense fallback={<div className="h-full w-full bg-black"></div>}>
      <DetailContent />
    </Suspense>
  );
}
