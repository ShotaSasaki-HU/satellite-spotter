// src/components/EventCard.tsx
import { Event } from "@/types/event";
import { MapPin, Star, Telescope, Cloud, Moon, Clock3, Satellite, Building2 } from "lucide-react";
import Link from "next/link";

interface EventCardProps {
  event: Event;
}

export default function EventCard({ event }: EventCardProps) {
  // 日付と時刻のフォーマット（ISO文字列 -> 見やすい形式へ）
  const startDate = new Date(event.start_time);
  const timeString = startDate.toLocaleTimeString("ja-JP", { 
    timeZone: "Asia/Tokyo",
    hour: "2-digit", 
    minute: "2-digit" 
  });
  const dateString = startDate.toLocaleDateString("ja-JP", { 
    timeZone: "Asia/Tokyo",
    month: "short", 
    day: "numeric",
    weekday: "short" // 曜日
  });

  // Googleマップの検索URL
  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${event.lat},${event.lon}`;

  // 総合評価を算出（例として visibility を 0〜100点として星評価っぽく見せる等。今回は数値をそのまま表示）
  const scoreValue = Math.round(event.scores.visibility * 100);

  return (
    <div className="bg-bg-primary border border-compass-gold/30 rounded-xl p-4 shadow-lg flex flex-col gap-3">
      {/* 上段 */}
      <div className="flex justify-between items-center border-b border-compass-gold/30 pb-2">
        <div className="min-w-0">
          {/* スポット名 */}
          <div className="flex items-center justify-start gap-1 text-lg">
            <MapPin size={20} className="text-compass-gold shrink-0" />
            <span className="truncate">{event.location_name || "あなただけの観測スポット"}</span>
          </div>

          {/* 開始日時 */}
          <div className="flex items-center justify-start gap-1 text-lg">
            <Clock3 size={20} className="text-compass-gold shrink-0" />
            <span className="truncate">{dateString} {timeString} ~</span>
          </div>

          {/* イベントタイプ */}
          <div className="flex items-center justify-start gap-1 text-lg">
            <Satellite size={20} className="text-compass-gold shrink-0" />
            <span className="truncate">{event.event_type}</span>
          </div>
        </div>

        {/* 観測スコア */}
        <div className="flex flex-col items-end">
          <span className="text-xs text-text-muted">観測スコア</span>
          <div className="text-2xl font-black text-text-primary flex items-center gap-1">
            <Star size={20} className="text-compass-gold fill-compass-gold" />
            {scoreValue}
            <span>点</span>
          </div>
        </div>
      </div>

      {/* 下段 */}
      <div className="flex justify-between items-center">
        <div className="flex flex-col md:flex-row gap-3 text-xs text-text-muted">
          <span className="flex items-center gap-1"><Building2 size={14} className="text-compass-gold shrink-0"/>光害：{100 - Math.round(event.scores.sky_glow * 100)}%</span>
          <span className="flex items-center gap-1"><Moon size={14} className="text-compass-gold shrink-0"/>月明かり：{100 - Math.round(event.scores.moon_fract_illumi * 100)}%</span>
          <span className="flex items-center gap-1"><Cloud size={14} className="text-compass-gold shrink-0"/>雲量：{100 - Math.round(event.scores.cloud * 100)}%</span>
        </div>

        {/* アクションボタン */}
        <div className="flex gap-2">
          {/* Google Mapsで開く（別タブ） */}
          <a 
            href={googleMapsUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-2 rounded-lg bg-compass-gray hover:bg-compass-gray-hover text-text-primary transition flex items-center gap-1 text-sm"
          >
            <MapPin size={16} />
            <span className="truncate"><span className="hidden md:inline">Google </span>マップ</span>
          </a>
          
          {/* 詳細（天球シミュレーション）へ */}
          <Link 
            // 実際はイベントのユニークIDなどを渡すのが望ましいですが、今回は時刻や座標をキーにします
            href={`/detail?lat=${event.lat}&lon=${event.lon}&time=${event.start_time}`} 
            className="p-2 rounded-lg bg-compass-gold hover:bg-compass-gold-hover text-text-primary transition flex items-center gap-1 text-sm"
          >
            <Telescope size={16} />
            <span className="whitespace-nowrap">詳細</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
