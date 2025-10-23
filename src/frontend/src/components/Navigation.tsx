// src/components/Navigation.tsx
"use client"; // 「今どのページにいるか」はブラウザ（クライアント）でないと判断できない．

import Link from "next/link"; // Next.jsのリンク機能．<a>タグより高速な画面遷移．
import { usePathname } from "next/navigation"; // usePathnameは，現在のURLのパス名を読み取れるクライアントコンポーネントフック
import { Search } from 'lucide-react';

// ナビゲーションの項目を配列で定義
// 後でループ処理（.map）を使ってボタンを自動生成できる．
const navItems = [
  { href: "/", label: "スポット検索", icon: "あ" },
  { href: "/my-spot", label: "マイスポット", icon: "あ" },
  { href: "/report", label: "観測レポート", icon: "あ" }
];

// コンポーネント定義．`export default`で他のファイルから`import`できる．
export default function Navigation() {
  const pathname = usePathname(); // 現在のURLパスを格納

  return (
    <nav
      className={`
        bg-blue-950 text-white z-50

        fixed bottom-0 left-0 w-full h-16
        flex flex-row justify-around items-center

        md:fixed md:left-0 md:top-0 md:w-48 md:h-screen
        md:flex-col md:justify-start md:items-stretch 
        md:pt-24
      `}
    >
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            prefetch={true} // 事前読み込み
            className={`
              flex items-center justify-center p-2
              hover:bg-blue-800 transition-colors

              flex-col text-xs

              md:flex-row md:justify-start md:text-base md:p-4

              ${isActive ? "text-yellow-400" : "text-gray-300"}
              ${isActive && "md:bg-blue-900"}
            `}
          >
            <span className="text-2xl md:mr-3">{item.icon}</span>
            <span className="hidden md:inline">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
