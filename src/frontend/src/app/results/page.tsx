// src/app/results/page.tsx
"use client";

import { useEffect, useState, Suspense, useCallback, use } from "react";
import { useSearchParams } from "next/navigation";
import { EventResponse, Event } from "@/types/event";
import EventCard from "@/components/EventCard";
import { Loader2, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useInView } from "react-intersection-observer";
import { useResultsCache } from "@/store/useResultsCache";

const LIMIT = 20; // 1回で取得するイベントの数（ページネーション用）

// 検索パラメータを使うコンポーネントは，Suspenseで囲むのがNext.jsのルールらしい．
function ResultsContent() {
  const searchParams = useSearchParams();
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const radius = searchParams.get("radius");
  const source = searchParams.get("source"); // どちらのページから来たか（SpotRecommenderPage or MySpotObserverPage）

  // source に応じて，APIと戻るURLを動的に決定する．
  const isMySpot = source === "my-spot";
  const apiEndpoint = isMySpot ? "/api/v1/forecasts/events" : "/api/v1/recommendations/events";
  const backUrl = isMySpot ? "/my-spot" : "/";

  // 結果のキャッシュを zustand から取得
  const cacheKey = useResultsCache((state) => state.cacheKey);
  const cacheEvents = useResultsCache((state) => state.events);
  const cacheTotal = useResultsCache((state) => state.total);
  const cacheOffset = useResultsCache((state) => state.offset);
  const setCache = useResultsCache((state) => state.setCache);
  // キャッシュキーと，現在のキーが一致するか確認．
  const currentKey = `${lat}-${lon}-${radius}-${source}`;
  const hasCache = cacheKey === currentKey && cacheEvents.length > 0;

  // キャッシュがあれば useState の初期値にを突っ込む．
  const [events, setEvents] = useState<Event[]>(hasCache ? cacheEvents : []);
  const [total, setTotal] = useState(hasCache ? cacheTotal : 0);
  const [offset, setOffset] = useState(hasCache ? cacheOffset : 0);

  const [loadingInitial, setLoadingInitial] = useState(!hasCache); // キャッシュがあれば初回のローディングは不要
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
    if (!lat || !lon) return;
    if (!isMySpot && !radius) return; // recommendationsの時はradius必須

    try {
      if (currentOffset === 0) {
        setLoadingInitial(true);
      } else {
        setLoadingMore(true);
      }

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${apiEndpoint}?lat=${lat}&lon=${lon}&radius=${radius}&limit=${LIMIT}&offset=${currentOffset}`
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
  }, [lat, lon, radius, apiEndpoint, isMySpot]);

  // 検索条件が変わった時：オフセットを0に戻して初回ロード
  useEffect(() => {
    if (hasCache) return; // キャッシュが一致すればAPIコールをスキップ

    setOffset(0);
    fetchEvents(0);
  }, [fetchEvents, hasCache]);

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

  // 結果のキャッシュ
  useEffect(() => {
    if (
      events.length > 0 &&
      (events.length === offset + LIMIT || events.length === total) // イベントの個数とオフセットの関係の妥当性を保証．最後のページでオフセットがLIMITの倍数でない場合も保存．
    ) {
      setCache(currentKey, events, total, offset);
    }
  }, [currentKey, events, total, offset, setCache]);

  return (
    <>
      {/* 動的に戻る場所が変わるヘッダー */}
      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <div className="w-full flex justify-center items-center gap-3">
          <Link href={backUrl}>
            <ChevronLeft size={30} className="text-compass-gray hover:text-compass-gray-hover" />
          </Link>
          <h1 className="text-compass-gold text-xl md:text-2xl">検索結果</h1>
        </div>
      </div>

      {/* スクロール領域 */}
      <div className="w-full h-full overflow-y-auto max-w-3xl mx-auto px-4 md:px-8 pt-16 pb-3">

        {loadingInitial ? (
          // 初回ローディング表示
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <Loader2 size={40} className="animate-spin text-compass-gold" />
            <p className="text-text-muted">いっしょうけんめい計算中...</p>
          </div>
        ) : error ? (
          // エラー表示
          <div className="text-red-500 p-4 bg-red-500/10 rounded-lg border border-compass-gold/30">{error}</div>
        ) : (
          // 結果リスト表示
          <div className="flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-end items-center mb-1">
              <span className="text-compass-gold text-lg">{total}件</span>
            </div>

            {events.length === 0 ? (
              <div className="text-center p-8 bg-bg-primary rounded-xl border border-compass-gold/30">
                <p className="text-text-muted">指定された条件で見えるイベントはありませんでした。</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {events.map((event, index) => (
                  <EventCard key={`${event.lat}-${event.lon}-${event.start_time}-${index}`} event={event} />
                ))}

                {events.length < total && (
                  <div ref={ref} className="w-full flex justify-center py-4">
                    {loadingMore && <Loader2 size={24} className="animate-spin text-compass-gold" />}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default function ResultsPage() {
  return (
    <div className="relative h-full w-full">
      <Suspense fallback={<div className="animate-pulse h-full w-full bg-bg-primary"></div>}>
        <ResultsContent />
      </Suspense>
    </div>
  );
}
