// src/app/detail/page.tsx
"use client";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { TrajectoryResponse } from "@/types/trajectory";
import { Loader2, ChevronLeft, Play, Pause, FastForward, Rewind } from "lucide-react";
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
  const locationName = searchParams.get("location_name") || "マイスポット";
  const lat = searchParams.get("lat");
  const lon = searchParams.get("lon");
  const startTime = searchParams.get("start_time");
  const endTime = searchParams.get("end_time");
  // クエリパラメータから配列を受け取るハック（URLSearchParams.getAll）
  const designators = searchParams.getAll("intldesg");

  const [data, setData] = useState<TrajectoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [timeIndex, setTimeIndex] = useState(0); // スライダーのインデックス
  const [isPlaying, setIsPlaying] = useState(true); // 再生状態
  const [playbackSpeed, setPlaybackSpeed] = useState(16); // 再生速度

  // 時間計算用のRef（値が変化しても再描画が起きない．）
  const lastUpdateRef = useRef<number>(0);
  const remainderMsRef = useRef<number>(0);

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

  // 再生のタイマー処理（requestAnimationFrame版）
  useEffect(() => {
    // 再生中でない，またはデータがない場合は何もしない．
    if (!isPlaying || !data || data.trajectories.length === 0) return;

    let animationFrameId: number;

    const tick = (timestamp: number) => {
      // 初回実行時の初期化
      if (!lastUpdateRef.current) lastUpdateRef.current = timestamp;

      // 前回のフレームから「現実の世界」で何ミリ秒経過したか
      const deltaRealMs = timestamp - lastUpdateRef.current;
      lastUpdateRef.current = timestamp;

      // 現実の経過時間に再生速度を掛けて「シミュレータ内の経過時間」を算出
      // （前回コマを進めきれずに余った時間も足し合わせる．）
      const deltaSimMs = (deltaRealMs * playbackSpeed) + remainderMsRef.current;

      setTimeIndex((prev) => {
        if (prev >= data.trajectories.length - 1) {
          setIsPlaying(false);
          return data.trajectories.length - 1;
        }

        let nextIndex = prev;
        let remainingSimMs = deltaSimMs;

        // 経過したシミュレータ時間分だけ，インデックスを「まとめ飛ばし」する．
        while (nextIndex < data.trajectories.length - 1) {
          const currentT = new Date(data.trajectories[nextIndex].timestamp).getTime();
          const nextT = new Date(data.trajectories[nextIndex + 1].timestamp).getTime();
          const diffMs = nextT - currentT;

          // 蓄積された時間が，次のコマまでの時間を上回っていたらコマを進める．
          if (remainingSimMs >= diffMs) {
            remainingSimMs -= diffMs;
            nextIndex++;
          } else {
            // 次のコマに進むほどの時間が貯まっていなければループを抜ける．
            break;
          }
        }

        // 使い切れなかった端数の時間は，次のフレームに持ち越す．
        remainderMsRef.current = remainingSimMs;
        return nextIndex;
      });

      animationFrameId = requestAnimationFrame(tick); // 次のフレーム描画を予約
    }; // tick関数の終わり

    animationFrameId = requestAnimationFrame(tick); // ループの初回起動のための呼び出し（起動したら関数tickが回り続ける．）

    // クリーンアップ関数（playbackSpeed等が変わったら，古いループをきちんと消す．）
    return () => {
      cancelAnimationFrame(animationFrameId);
      lastUpdateRef.current = 0; // effect終了時にリセット
    };
  }, [isPlaying, playbackSpeed, data]);

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
        <SkySimulator
          currentPositions={currentTrajectory.positions}
          currentTimeIso={currentTrajectory.timestamp}
          lat={Number(lat)}
          lon={Number(lon)}
          allTrajectories={data.trajectories}
        />
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
            <ChevronLeft size={30} className="text-compass-gray hover:text-compass-gray-hover" />
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

        <div className="relative flex justify-center items-center text-xs text-text-muted mt-1">
          <Rewind
            size={18}
            className="mr-4 text-compass-gold hover:text-compass-gold-hover cursor-pointer"
            onClick={() => setPlaybackSpeed((prev) => Math.max(1, prev / 2))}
          />

          {isPlaying ? (
            <button onClick={() => setIsPlaying(false)} className="text-compass-gold hover:text-compass-gold-hover cursor-pointer">
              <Pause size={20} />
            </button>
          ) : (
            <button
              onClick={() => {
                // 最後まで到達している状態でPlayを押されたら最初から再生する．
                if (data && timeIndex >= data.trajectories.length - 1) {
                  setTimeIndex(0);
                }
                setIsPlaying(true);
              }}
              className="text-compass-gold hover:text-compass-gold-hover cursor-pointer"
            >
              <Play size={20} />
            </button>
          )}

          <FastForward
            size={18}
            className="ml-4 text-compass-gold hover:text-compass-gold-hover cursor-pointer"
            onClick={() => setPlaybackSpeed((prev) => Math.min(128, prev * 2))}
          />

          <span className="absolute left-1/2 ml-14 text-text-muted text-lg tracking-wider">{playbackSpeed}×</span>
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
