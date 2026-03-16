// src/components/SkySimulator.tsx
"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sky, OrbitControls, Stars, Text } from "@react-three/drei";
import * as THREE from "three";
import { Position } from "@/types/trajectory";
import { useSimulationStore } from "@/store/useSimulationStore";

interface SkySimulatorProps {
  currentPositions: Position[];
}

// 衛星1つ1つを描画してチカチカさせるコンポーネント
function SatellitePoint({ pos }: { pos: Position }) {
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
      <sphereGeometry args={[0.5, 16, 16]} />
      {/* 衛星の光（ゴールド系） */}
      <meshBasicMaterial
        ref={materialRef}
        color="#d4af37"
        transparent
        opacity={1}
      />
      {/* 衛星のラベル */}
      <Text
        position={[0, 1.5, 0]}
        rotation={[0, -azRad, 0]} // ラベルが常に読めるように回転
        fontSize={1}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {pos.international_designator}
      </Text>
    </mesh>
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
      
      {/* 稜線をなぞるゴールドの輪郭線 */}
      <lineSegments geometry={edgesGeometry}>
        <lineBasicMaterial color="#d4af37" transparent opacity={0.5} />
      </lineSegments>
    </group>
  );
}

export default function SkySimulator({ currentPositions }: SkySimulatorProps) {
  const { horizonProfile } = useSimulationStore();

  const RADIUS_LABEL = 48;
  const LABEL_SIZE = 2;
  const LABEL_Y = 2;

  return (
    <Canvas camera={{ position: [0, 0.01, 0], fov: 75 }}
    >
      {/* ユーザーがドラッグでぐるぐる見渡せるようにする（地下には行けないよう制限） */}
      {/* PolarAngle: おそらく真下が0度で真上が180度 */}
      <OrbitControls 
        enablePan={false} 
        enableZoom={false}
        minPolarAngle={THREE.MathUtils.degToRad(75)}
        maxPolarAngle={Math.PI}
      />
      
      {/* リアルな星空と夜空の背景 */}
      <Sky distance={450000} sunPosition={[0, -1, 0]} inclination={0} azimuth={0.25} />
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      
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

      {/* 現在時刻の衛星たちを描画 */}
      {currentPositions.map((pos) => (
        <SatellitePoint key={pos.international_designator} pos={pos} />
      ))}
    </Canvas>
  );
}
