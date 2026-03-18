// src/components/SkySimulator.tsx
"use client";

import { useRef, useMemo, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sky, OrbitControls, Text, Billboard, Line } from "@react-three/drei";
import * as THREE from "three";
import { SatPosition, Trajectory } from "@/types/trajectory";
import { StarPosition } from "@/types/star";
import { useSimulationStore } from "@/store/useSimulationStore";

interface SkySimulatorProps {
  currentPositions: SatPosition[];
  currentTimeIso: string;
  lat: number;
  lon: number;
  allTrajectories: Trajectory[];
}

// 値の変更を遅延させるカスタムフック
function useDebounce<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // delayMs 経過後に初めて state を更新するタイマーをセット
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    // 値が連続で変わった場合（スライダーをグリグリしている最中）は，前のタイマーをキャンセルしてタイマーをリセットする．
    return () => {
      clearTimeout(handler);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

function RealStars({ timeIso, lat, lon }: { timeIso: string, lat: number, lon: number }) {
  const [stars, setStars] = useState<StarPosition[]>([]);
  const RADIUS = 100; // 衛星(50)より奥に配置する

  // ミリ秒単位でAPIを叩かないよう，時間を丸めて扱う．
  const roundedTimeIso = useMemo(() => {
    const date = new Date(timeIso);
    date.setSeconds(0, 0); // 1分単位で丸める．
    return date.toISOString();
  }, [timeIso]);

  // 丸めた時間をさらに「デバウンス」にかける．スライダーが止まってから，Nミリ秒後に初めて値が確定する．
  const debouncedTimeIso = useDebounce(roundedTimeIso, 250);

  // さらに AbortController を使って，直前の不要な通信を撃墜する．
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const fetchStars = async () => {
      // 既に走っている通信があればキャンセル
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      try {
        const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/stars?time=${encodeURIComponent(roundedTimeIso)}&lat=${lat}&lon=${lon}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("星空の取得に失敗しました");
        const data = await res.json();
        setStars(data.positions);
      } catch (error: any) {
        if (error.name === "AbortError") {
          console.log("星空の古いリクエストをキャンセルしました");
          return;
        }
        console.error("星空エラー:", error);
      }
    };

    fetchStars();
  }, [debouncedTimeIso, lat, lon]);

  return (
    <group>
      {stars.map((star, idx) => {
        const azRad = THREE.MathUtils.degToRad(star.az);
        const altRad = THREE.MathUtils.degToRad(star.alt);
        const x = RADIUS * Math.cos(altRad) * Math.sin(azRad);
        const y = RADIUS * Math.sin(altRad);
        const z = -RADIUS * Math.cos(altRad) * Math.cos(azRad);

        // 等級（1〜4.5）に応じて，星の大きさを変える．（数字が小さいほど明るく大きい）
        const size = Math.max(0.2, 0.59 - (star.magnitude * 0.086));
        // 0.5 = a + b.  , 2.25 = 4.5a + 4.5b
        // 0.2 = 4.5a + b, 0.2 = 4.5a + b
        // b = 2.05 / 3.5, a = 0.5 - (2.05 / 3.5)
        // a = -0.086, b = 0.59

        // 等級に応じて透明度も変える．
        const opacity = Math.max(0.3, 1.2 - (star.magnitude * 0.2));
        // 1 = a + b
        // 0.3 = 4.5a + b, 0.3 = 4.5a + 1 - a
        // a = -0.7 / 3.5 = -0.2, b = 1.2

        return (
          <group key={`${star.star_name}-${idx}`} position={[x, y, z]}>
            {/* 星の光点 */}
            <mesh>
              <sphereGeometry args={[size, 8, 8]} />
              <meshBasicMaterial color="#ffffff" opacity={opacity} />
            </mesh>

            {/* 星のラベル（固有名がある場合のみ） */}
            {star.star_name !== "" && (
              // Billboardコンポーネントは，勝手にカメラの方を向く．
              <Billboard
                follow={true}
                lockX={false}
                lockY={false}
                lockZ={false}
              >
                <Text
                  position={[0, 2, 0]} // 星の少し上に配置
                  fontSize={2}
                  color="white"
                  anchorX="center"
                  anchorY="middle"
                >
                  {star.star_name}
                </Text>
              </Billboard>
            )}
          </group>
        );
      })}
    </group>
  );
}

// 衛星1つ1つを描画してチカチカさせるコンポーネント
function SatellitePoint({ pos }: { pos: SatPosition }) {
  const materialRef = useRef<THREE.MeshBasicMaterial>(null);

  // Az(方位角)とAlt(仰俯角)を3D空間のXYZ座標に変換する極座標計算
  // 北(az=0)を -Z方向，東(az=90)を +X方向，天頂(alt=90)を +Y方向とする．
  const RADIUS = 50; // 天球の半径
  const azRad = THREE.MathUtils.degToRad(pos.az);
  const altRad = THREE.MathUtils.degToRad(pos.alt);

  const x = RADIUS * Math.cos(altRad) * Math.sin(azRad);
  const y = RADIUS * Math.sin(altRad);
  const z = -RADIUS * Math.cos(altRad) * Math.cos(azRad);

  // 毎フレーム実行される処理（チカチカさせるアニメーション）
  useFrame(({ clock }) => {
    if (materialRef.current) {
      // サイン波を使って，透明度を 0.3 〜 1.0 の間でフワフワと往復させる．
      materialRef.current.opacity = 0.65 + 0.35 * Math.sin(clock.elapsedTime * 4);
    }
  });

  return (
    <mesh position={[x, y, z]}>
      {/* サイズ：0.5 */}
      <sphereGeometry args={[0.5, 16, 16]} />

      {/* 衛星の光（ゴールド系） */}
      <meshBasicMaterial
        ref={materialRef}
        color="#d4af37"
        transparent
        opacity={1}
      />
      {['98067A', '21066A'].includes(pos.international_designator) && (
        // Billboardコンポーネントは，勝手にカメラの方を向く．
        <Billboard
          follow={true}
          lockX={false}
          lockY={false}
          lockZ={false}
        >
          <Text
            position={[0, 1.5, 0]} // 星の少し上に配置
            fontSize={1.0}
            color="white"
            anchorX="center"
            anchorY="middle"
          >
            国際宇宙ステーション
          </Text>
        </Billboard>
      )}
    </mesh>
  );
}

// 代表衛星1機だけの「軌跡の線」を描画するコンポーネント
function RepresentativeTrajectory({ allTrajectories }: { allTrajectories: Trajectory[] }) {
  const RADIUS = 50;

  const points = useMemo(() => {
    // 1. 代表となる衛星のIDを決定（最初に見つかった衛星をターゲットにする．）
    let targetId: string | null = null;
    for (const traj of allTrajectories) {
      if (traj.positions.length > 0) {
        targetId = traj.positions[0].international_designator;
        break;
      }
    }

    if (!targetId) return [];

    const coords: [number, number, number][] = [];

    // 2. 全時刻のデータから，代表衛星の座標だけを抽出して配列にする．
    for (const traj of allTrajectories) {
      const pos = traj.positions.find((p: SatPosition) => p.international_designator === targetId);
      if (pos) {
        const azRad = THREE.MathUtils.degToRad(pos.az);
        const altRad = THREE.MathUtils.degToRad(pos.alt);
        const x = RADIUS * Math.cos(altRad) * Math.sin(azRad);
        const y = RADIUS * Math.sin(altRad);
        const z = -RADIUS * Math.cos(altRad) * Math.cos(azRad);

        coords.push([x, y, z]);
      }
    }
    return coords;
  }, [allTrajectories]);

  // 点が2つ以上ないと線が引けないためガード
  if (points.length < 2) return null;

  return (
    <>
      <mesh position={points[Math.floor(points.length / 2)]}>
        <Billboard follow={true} lockX={false} lockY={false} lockZ={false}>
          <Text
            position={[0, 1.5, 0]}
            fontSize={1.0}
            color="#fde047"
            anchorX="center"
            anchorY="middle"
          >
            軌道の目安
          </Text>
        </Billboard>
      </mesh>

      <Line
        points={points}
        color="#fde047" // 衛星本体と合わせた少し明るめのゴールド
        lineWidth={2} // 線の太さ
        transparent
        opacity={0.3}   // 星空の邪魔にならないよう薄めに設定
        dashed={true}   // 点線にする
        dashScale={30}  // 破線の間隔スケール
        dashSize={5}
        gapSize={5}
      />
    </>
  );
}

// 地平線のシルエットを描画するコンポーネント
function HorizonSilhouette({ profile }: { profile: number[] | null }) {
  // 毎フレーム計算すると重いので、データが変わった時だけジオメトリを生成する（useMemo）
  const geometry = useMemo(() => {
    // データが無い場合は、ただの「平地（仰角0度）」のダミー配列を作る
    const data = profile && profile.length > 0 ? profile : [0, 0, 0, 0, 0, 0, 0, 0];
    const N = data.length;

    // 衛星は，RADIUS=50．
    const RADIUS_HORIZON = 49;

    const positions = []; // 頂点のXYZ座標
    const indices = []; // 頂点を結んで三角形を作る順番

    // 0 から N までループ（最後は 0 度に戻って壁を閉じるため i <= N とする）
    for (let i = 0; i <= N; i++) {
      // 方位角（az）を計算。i=0なら0度、i=Nなら360度
      const az = (i / N) * 360;
      // 仰角（alt）を取得。最後の要素は0番目と同じ高さにする
      const alt = i === N ? data[0] : data[i];

      const azRad = THREE.MathUtils.degToRad(az);
      const topAltRad = THREE.MathUtils.degToRad(alt);
      const bottomAltRad = THREE.MathUtils.degToRad(0); // 地面は仰角0度とする．

      // 頂点A：稜線上の点（上）
      positions.push(
        RADIUS_HORIZON * Math.cos(topAltRad) * Math.sin(azRad),
        RADIUS_HORIZON * Math.sin(topAltRad),
        -RADIUS_HORIZON * Math.cos(topAltRad) * Math.cos(azRad)
      );

      // 頂点B：地面の点（下）
      positions.push(
        RADIUS_HORIZON * Math.cos(bottomAltRad) * Math.sin(azRad),
        RADIUS_HORIZON * Math.sin(bottomAltRad),
        -RADIUS_HORIZON * Math.cos(bottomAltRad) * Math.cos(azRad)
      );

      // ポリゴン生成：隣り合う頂点を結んで四角形（三角形 * 2）を作る．
      if (i < N) {
        const tl = 2 * i;           // 左上
        const bl = 2 * i + 1;       // 左下
        const tr = 2 * (i + 1);     // 右上
        const br = 2 * (i + 1) + 1; // 右下

        indices.push(tl, bl, tr); // 三角形1
        indices.push(tr, bl, br); // 三角形2
      }
    }

    // Three.jsのジオメトリオブジェクトに組み立てる
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geom.setIndex(indices);
    geom.computeVertexNormals();
    return geom;
  }, [profile]);

  // ポリゴンの上辺（稜線）だけを抽出した線（EdgesGeometry）を作る
  const edgesGeometry = useMemo(() => {
    return new THREE.EdgesGeometry(geometry, 1); // 角度の閾値を調整して稜線だけを抽出
  }, [geometry]);

  return (
    <group>
      {/* 黒いシルエット本体 */}
      <mesh geometry={geometry}>
        {/* opacityで星空を少しだけ透けさせる */}
        <meshBasicMaterial color="#0f172a" side={THREE.DoubleSide} transparent opacity={0.85} />
      </mesh>
    </group>
  );
}

export default function SkySimulator({ currentPositions, currentTimeIso, lat, lon, allTrajectories }: SkySimulatorProps) {
  const { horizonProfile } = useSimulationStore();

  const RADIUS_LABEL = 48;
  const LABEL_SIZE = 2;
  const LABEL_Y = 2;

  return (
    <Canvas camera={{ position: [0, 0.01, 0], fov: 75 }}>
      {/* ユーザーがドラッグでぐるぐる見渡せるようにする（地下には行けないよう制限） */}
      {/* PolarAngle: おそらく真下が0度で真上が180度 */}
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        minPolarAngle={THREE.MathUtils.degToRad(75)}
        maxPolarAngle={Math.PI}
        rotateSpeed={-0.5}
      />

      {/* リアルな星空と夜空の背景 */}
      <Sky distance={450000} sunPosition={[0, -1, 0]} inclination={0} azimuth={0.25} />
      <RealStars timeIso={currentTimeIso} lat={lat} lon={lon} />

      {/* 地面（方角の目安となるグリッド） */}
      <gridHelper args={[200, 50, "#444", "#222"]} position={[0, -0.1, 0]} />

      {/* 方角ラベル */}
      <Text position={[RADIUS_LABEL * Math.sin(Math.PI), LABEL_Y, RADIUS_LABEL * Math.cos(Math.PI)]} fontSize={LABEL_SIZE} color="white" rotation={[0, 0, 0]}>北</Text>
      <Text position={[RADIUS_LABEL * Math.sin(Math.PI * 3 / 4), LABEL_Y, RADIUS_LABEL * Math.cos(Math.PI * 3 / 4)]} fontSize={LABEL_SIZE} color="white" rotation={[0, - Math.PI / 4, 0]}>北東</Text>
      <Text position={[RADIUS_LABEL * Math.sin(Math.PI / 2), LABEL_Y, RADIUS_LABEL * Math.cos(Math.PI / 2)]} fontSize={LABEL_SIZE} color="white" rotation={[0, - Math.PI / 2, 0]}>東</Text>
      <Text position={[RADIUS_LABEL * Math.sin(Math.PI / 4), LABEL_Y, RADIUS_LABEL * Math.cos(Math.PI / 4)]} fontSize={LABEL_SIZE} color="white" rotation={[0, - Math.PI * 3 / 4, 0]}>南東</Text>
      <Text position={[RADIUS_LABEL * Math.sin(0), LABEL_Y, RADIUS_LABEL * Math.cos(0)]} fontSize={LABEL_SIZE} color="white" rotation={[0, Math.PI, 0]}>南</Text>
      <Text position={[RADIUS_LABEL * Math.sin(- Math.PI / 4), LABEL_Y, RADIUS_LABEL * Math.cos(- Math.PI / 4)]} fontSize={LABEL_SIZE} color="white" rotation={[0, Math.PI * 3 / 4, 0]}>南西</Text>
      <Text position={[RADIUS_LABEL * Math.sin(- Math.PI / 2), LABEL_Y, RADIUS_LABEL * Math.cos(- Math.PI / 2)]} fontSize={LABEL_SIZE} color="white" rotation={[0, Math.PI / 2, 0]}>西</Text>
      <Text position={[RADIUS_LABEL * Math.sin(- Math.PI * 3 / 4), LABEL_Y, RADIUS_LABEL * Math.cos(Math.PI * 3 / 4)]} fontSize={LABEL_SIZE} color="white" rotation={[0, Math.PI / 4, 0]}>北西</Text>

      <HorizonSilhouette profile={horizonProfile} />

      <RepresentativeTrajectory allTrajectories={allTrajectories} />

      {/* 現在時刻の衛星たちを描画 */}
      {currentPositions.map((pos) => (
        <SatellitePoint key={pos.international_designator} pos={pos} />
      ))}
    </Canvas>
  );
}
