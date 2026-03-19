// src/app/help/page.tsx
import { MapPin, Telescope, Star, Search, Sparkles, MousePointerClick } from "lucide-react";

export default function ReportPage() {
  return (
    <div className="relative w-full h-full">
      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <h1 className="text-compass-gold text-xl md:text-2xl">使い方</h1>
      </div>

      {/* メインコンテンツ */}
      <div className="pt-24 pb-12 px-6 md:px-12 max-w-3xl mx-auto space-y-12 h-full overflow-y-auto">

        {/* イントロダクション */}
        <section className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
          <h2 className="text-xl text-white font-bold flex items-center gap-2 mb-4">
            <Sparkles className="text-compass-gold" size={24} />
            人工衛星は、肉眼で見えます。
          </h2>
          <p className="leading-relaxed text-sm md:text-base">
            夜空をスーッと動く光の点。実はそれ、宇宙を飛ぶ人工衛星かもしれません。
            太陽の光を反射して輝くため、<strong className="text-white">日没後や日の出前の数時間</strong>だけ、肉眼でハッキリと見ることができます。
            <br /><br />
            <span className="text-sm text-slate-400">
              ※飛行機のようにチカチカ点滅はしません。音もなく、星がそのまま動いていくように見えます。
            </span>
          </p>
        </section>

        {/* アプリの機能 */}
        <section>
          <h3 className="text-xl text-compass-gold mb-6 border-b border-compass-gold/30 pb-2">
            ２つの探し方
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-bg-primary border border-slate-700 p-5 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <Search className="text-compass-gold" size={20} />
                <h4 className="text-white font-bold">スポット検索</h4>
              </div>
              <p className="text-sm text-slate-400">
                あらかじめ登録されている公園などの観測スポットから、手軽に予報を探すことができます。
              </p>
            </div>
            <div className="bg-bg-primary border border-slate-700 p-5 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <MousePointerClick className="text-compass-gold" size={20} />
                <h4 className="text-white font-bold">マイスポット</h4>
              </div>
              <p className="text-sm text-slate-400">
                地図上にピンを刺して、自宅や今いる場所から衛星が見えるかを計算できる機能です。
              </p>
            </div>
          </div>
        </section>

        {/* ステップ解説 */}
        <section>
          <h3 className="text-xl text-compass-gold mb-6 border-b border-compass-gold/30 pb-2">
            観測までの３ステップ
          </h3>

          <div className="space-y-6">
            {/* Step 1 */}
            <div className="flex gap-4 items-start">
              <div className="bg-bg-primary p-3 rounded-full border border-slate-700 shrink-0">
                <MapPin className="text-compass-gold" size={24} />
              </div>
              <div>
                <h4 className="text-white font-bold mb-1">１．行動範囲・場所を決める</h4>
                <p className="text-sm">
                  「スポット検索」なら、まず行動範囲を決めます。「マイスポット」なら、観測したい場所をピンポイントで指定します。明るい都会から遠く、空が開けている場所がおすすめです。
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4 items-start">
              <div className="bg-bg-primary p-3 rounded-full border border-slate-700 shrink-0">
                <Star className="text-compass-gold" size={24} />
              </div>
              <div>
                <h4 className="text-white font-bold mb-1">２．予報をチェックする</h4>
                <p className="text-sm">
                  「どこで」「いつ」「どんな衛星が」見えるかの予報リストが表示されます。「観測スコア」が１００点に近いほど、天気などの条件が良く、衛星を見つけやすいです。
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4 items-start">
              <div className="bg-bg-primary p-3 rounded-full border border-slate-700 shrink-0">
                <Telescope className="text-compass-gold" size={24} />
              </div>
              <div>
                <h4 className="text-white font-bold mb-1">３．「見えかた」画面で予行演習</h4>
                <p className="text-sm">
                  「詳細」ボタンを押すと、実際の地平線と星空を背景に、衛星の位置・通るルートが金色で表示されます。スライダーを動かして、どの星の近くを通るか確認したら、あとは夜空を見上げるだけです！
                </p>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  )
}
