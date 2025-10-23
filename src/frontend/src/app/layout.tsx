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
  title: "サテライト・スポッター",
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
        className={`${inter.className}
          bg-black text-white min-h-screen
          border-8 border-yellow-500 box-border
        `} // box-border: 枠線のせいでスクロールバーが出るのを防止
      >
        {/* ナビゲーションとメインコンテンツを包むラッパー */}
        <div className="flex flex-col md:flex-row">
          {/* 共通ナビゲーション */}
          <Navigation />

          {/* メインコンテンツ */}
          <main className="w-full pb-16 md:pl-48 md:pb-0">
            {/* コンテンツが画面端に接触しないための余白 */}
            <div className="p-4">
              {/* ページの中身をココに挿入 */}
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
