// src/app/layout.tsx
// 全ページ共通の土台
import type { Metadata } from "next"; // メタデータの型定義をインポート
import { Inter } from "next/font/google"; // フォントをインポート
import "./globals.css";
import Navigation from "@/components/Navigation";

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
          bg-bg-secondary text-text-primary min-h-screen
          border-8 border-compass-gold
        `}
      >
        {/* ナビゲーションとメインコンテンツを包むラッパー */}
        <div className="flex flex-col md:flex-row">
          {/* 共通ナビゲーション */}
          <Navigation />

          {/* メインコンテンツ */}
          {/* Navigationの分だけレスポンシブにpadding */}
          <main className="w-full pb-16 md:pl-48 md:pb-0">
            {/* ページの中身をココに挿入 */}
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
