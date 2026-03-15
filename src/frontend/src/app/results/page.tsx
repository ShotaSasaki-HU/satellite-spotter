// src/app/results/page.tsx
"use client";

import { useEffect, useState, Suspense, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { EventResponse, Event } from "@/types/event";
import EventCard from "@/components/EventCard";
import { Loader2, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useInView } from "react-intersection-observer";

const LIMIT = 20; // 1回で取得するイベントの数（ページネーション用）

// 検索パラメータを使うコンポーネントは，Suspenseで囲むのがNext.jsのルールらしい．
function ResultsContent() {
  const searchParams = useSearchParams();
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const radius = searchParams.get("radius");

  const [events, setEvents] = useState<Event[]>([]); // イベントを上書きではなく追加していくため配列
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  const [loadingInitial, setLoadingInitial] = useState(true); // 初回のローディング
  const [loadingMore, setLoadingMore] = useState(false); // 追加取得中のローディング
  const [error, setError] = useState("");

  // 無限スクロールのセンサー
  // ref: 監視したいHTML要素につける目印
  // inView: その要素が画面内に入ったら true になる魔法のフラグ
  const { ref, inView } = useInView({
    rootMargin: "200px", // 画面に入る200px手前で早めにロードを開始
  });

  // データ取得ロジック（初回も追加もこれを使う）
  const fetchEvents = useCallback(async (currentOffset: number) => {
    if (!lat || !lon || !radius) return;

    try {
      if (currentOffset === 0) {
        setLoadingInitial(true);
      } else {
        setLoadingMore(true);
      }

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/recommendations/events?lat=${lat}&lon=${lon}&radius=${radius}&limit=${LIMIT}&offset=${currentOffset}`
      );
      if (!res.ok) throw new Error("データの取得に失敗しました");
      
      const result: EventResponse = await res.json();
      
      setTotal(result.total);
      
      // オフセットが0（初回）なら配列をリセット、それ以外なら既存の配列に末尾追加
      if (currentOffset === 0) {
        setEvents(result.events);
      } else {
        setEvents((prev) => [...prev, ...result.events]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingInitial(false);
      setLoadingMore(false);
    }
  }, [lat, lon, radius]);

  // 検索条件が変わった時：オフセットを0に戻して初回ロード
  useEffect(() => {
    setOffset(0);
    fetchEvents(0);
  }, [fetchEvents]);

  // センサーが画面に入った時：次のデータをロード
  useEffect(() => {
    // センサーが見えていて，ロード中でなくて，まだ取得できるデータが残っている場合のみ発火．
    if (inView && !loadingInitial && !loadingMore && events.length < total) {
      const nextOffset = offset + LIMIT;
      setOffset(nextOffset);
      fetchEvents(nextOffset);
    }
  }, [inView, loadingInitial, loadingMore, events.length, total, offset, fetchEvents]);
  // useEffectは，監視対象にされてない変数の変更を無視し，古い値を使い続ける．よって，依存している変数は全て監視させる．

  if (loadingInitial) {
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
        <span className="text-compass-gold text-lg">{total}件</span>
      </div>

      {events.length === 0 ? (
        <div className="text-center p-8 bg-bg-primary rounded-xl border border-white/10">
          <p className="text-text-muted">指定された条件で見えるイベントはありませんでした。</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {events.map((event, index) => (
            // リストのキーには一意な値が必要です（今回は時間と座標の組み合わせ等を使用）
            <EventCard key={`${event.lat}-${event.lon}-${event.start_time}-${index}`} event={event} />
          ))}

          {/* 無限スクロールの「底」 */}
          {events.length < total && (
            <div ref={ref} className="w-full flex justify-center py-4">
              {loadingMore && <Loader2 size={24} className="animate-spin text-compass-gold" />}
            </div>
          )}
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
