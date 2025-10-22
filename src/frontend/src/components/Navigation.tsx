// src/components/Navigation.tsx
// スマホで下タブ，パソコンで左タブを実現するレスポンシブ部品

"use client"; // 「今どのページにいるか」はブラウザ（クライアント）でないと判断できない．

import Link from "next/link"; // Next.jsのリンク機能．<a>タグより高速な画面遷移．
import { usePathname } from "next/navigation"; // usePathnameは，現在のURLのパス名を読み取れるクライアントコンポーネントフック

// ナビゲーションの項目を配列で定義
// 後でループ処理（.map）を使ってボタンを自動生成できる．
const navItems = [
    { href: "/", label: "スポット検索", icon: "" },
    { href: "/my-spot", label: "マイスポット", icon: "" },
    { href: "/report", label: "観測レポート", icon: "" }
];

// コンポーネント定義．`export default`で他のファイルから`import`できる．
export default function Navigation() {
    const pathname = usePathname(); // 現在のURLパスを格納

    return (
        <nav
            className="
                bg-blue-950 text-white z-50
                
                fixed bottom-0 left-0 w-full h-16
                flex flex-row justify-around items-center

                md:fixed md:left-0 md:top-0 md:w-48 md:h-screen
                md:flex-col md:justify-start md:items-stretch
                md:pt-24
            "
        >
            {navItems.map((item) => {
                const isActive = pathname === item.href;

                return(
                    <Link
                        key={item.href}
                    ></Link>
                );
            })}
        </nav>
    );
}
