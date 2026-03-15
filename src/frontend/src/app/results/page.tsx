// src/app/results/page.tsx
"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { EventResponse } from "@/types/event";
import EventCard from "@/components/EventCard";
import { Loader2, ChevronLeft } from "lucide-react";
import Link from "next/link";

// 検索パラメータを使うコンポーネントは，Suspenseで囲むのがNext.jsのルールらしい．
function ResultsContent() {
  const searchParams = useSearchParams();
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const radius = searchParams.get("radius");

  const [data, setData] = useState<EventResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!lat || !lon || !radius) return;

    const fetchEvents = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/recommendations/events?lat=${lat}&lon=${lon}&radius=${radius}`);
        if (!res.ok) throw new Error("データの取得に失敗しました");
        
        const result: EventResponse = await res.json();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [lat, lon, radius]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <Loader2 size={40} className="animate-spin text-compass-gold" />
        <p className="text-text-muted">最適な観測スポットを計算中...</p>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 p-4 bg-red-500/10 rounded-lg border border-red-500/20">{error}</div>;
  }

  return (
    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500 mt-10">
      {/* ヒット件数 */}
      <div className="flex justify-end items-center">
        <span className="text-compass-gold text-lg">{data?.total || 0}件</span>
      </div>

      {data?.events.length === 0 ? (
        <div className="text-center p-8 bg-bg-primary rounded-xl border border-white/10">
          <p className="text-text-muted">指定された条件で見えるイベントはありませんでした。</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {data?.events.map((event, index) => (
            // リストのキーには一意な値が必要です（今回は時間と座標の組み合わせ等を使用）
            <EventCard key={`${event.lat}-${event.lon}-${event.start_time}-${index}`} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <div className="relative h-full w-full">
      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <div className="w-full flex justify-center items-center gap-3">
          {/* トップへ戻るボタン（Zustandが入力値を記憶しているので，前回の状態で表示される．） */}
          <Link href="/">
            <ChevronLeft size={30} className="text-compass-gray hover:text-compass-gray-hover"/>
          </Link>
          <h1 className="text-compass-gold text-xl md:text-2xl">検索結果</h1>
        </div>
      </div>

      <div className="w-full h-full overflow-y-auto p-4 md:p-8 max-w-3xl mx-auto">
        <Suspense fallback={<div className="animate-pulse h-32 bg-bg-primary rounded-xl"></div>}>
          <ResultsContent />
        </Suspense>
      </div>
    </div>
  );
}
