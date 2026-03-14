// src/components/Navigation.tsx
"use client"; // 「今どのページにいるか」はブラウザ（クライアント）でないと判断できない．

import Link from "next/link"; // Next.jsのリンク機能．<a>タグより高速な画面遷移．
import { usePathname } from "next/navigation"; // usePathnameは，現在のURLのパス名を読み取れるクライアントコンポーネントフック
import { Search, MousePointerClick, UsersRound } from 'lucide-react';

// ナビゲーションの項目を配列で定義
// 後でループ処理（.map）を使ってボタンを自動生成できる．
const navItems = [
  { href: "/", label: "スポット検索", icon: <Search className="w-8 h-8 md:w-6 md:h-6"/> },
  { href: "/my-spot", label: "マイスポット", icon: <MousePointerClick className="w-8 h-8 md:w-6 md:h-6"/> },
  { href: "/report", label: "観測レポート", icon: <UsersRound className="w-8 h-8 md:w-6 md:h-6"/> }
];

// コンポーネント定義．`export default`で他のファイルから`import`できる．
export default function Navigation() {
  const pathname = usePathname(); // 現在のURLパスを格納

  return (
    <nav
      className={`
        bg-bg-primary text-text-primary z-1000

        fixed bottom-2 left-2 w-[calc(100%-16px)] h-16
        flex flex-row justify-around items-center
        divide-x divide-compass-gold

        md:fixed md:left-2 md:top-2 md:w-48 md:h-[calc(100%-16px)]
        md:flex-col md:justify-start md:items-stretch
        md:divide-x-0
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
              flex items-center justify-center p-2 w-full

              flex-col text-xs h-full

              md:flex-row md:justify-start md:text-base md:p-4 md:h-auto

              ${isActive ? "text-compass-gold bg-bg-primary-active" :
                "text-text-muted hover:bg-bg-primary-hover"}
            `}
          >
            <span className="md:mr-3">{item.icon}</span>
            <span className="hidden md:inline">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
