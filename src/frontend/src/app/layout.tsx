// src/app/layout.tsx
// 全ページ共通の土台
import type { Metadata } from "next"; // メタデータの型定義をインポート
import { Inter } from "next/font/google"; // フォントをインポート
import "./globals.css";
import Navigation from "@/components/Navigation";
import { Satellite } from 'lucide-react';

// アルファベットのみInterフォントで表示
const inter = Inter({ subsets: ["latin"] });

// サイトのメタデータを定義
export const metadata: Metadata = {
  title: "Satellite Spotter",
  description: "あなただけの衛星観測スポットを見つけよう！",
};

// ルートレイアウトコンポーネント
export default function RootLayout({
  children, // このPropsに，各page.tsxの中身が自動的に挿入される．
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body
        className={`
          ${inter.className}
          bg-bg-secondary text-text-primary h-dvh
          border-8 border-compass-gold
          select-none
        `}
      >
        {/* ナビゲーションとメインコンテンツを包むラッパー */}
        <div className="h-full flex flex-col md:flex-row">
          {/* 共通ナビゲーション */}
          <Navigation />

          {/* メインコンテンツ */}
          {/* Navigationの分だけレスポンシブにpadding */}
          <main className="relative w-full h-full pb-16 md:pl-48 md:pb-0">
            <div className="absolute top-3 right-3 flex items-center z-1000 drop-shadow-lg/75">
              <Satellite className="w-6 h-6 md:w-9 md:h-9 text-text-primary"/>
              <span className="ml-2 text-text-primary text-base md:text-2xl">Satellite Spotter</span>
            </div>

            {/* ページの中身をココに挿入 */}
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
