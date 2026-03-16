// src/components/SkySimulator.tsx
"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sky, OrbitControls, Stars, Text } from "@react-three/drei";
import * as THREE from "three";
import { Position } from "@/types/trajectory";

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

export default function SkySimulator({ currentPositions }: SkySimulatorProps) {
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
      <Text position={[50 * Math.sin(Math.PI), 3, 50 * Math.cos(Math.PI)]} fontSize={3} color="white" rotation={[0, 0, 0]}>北</Text>
      <Text position={[50 * Math.sin(Math.PI * 3 / 4), 3, 50 * Math.cos(Math.PI * 3 / 4)]} fontSize={3} color="white" rotation={[0, - Math.PI / 4, 0]}>北東</Text>
      <Text position={[50 * Math.sin(Math.PI / 2), 3, 50 * Math.cos(Math.PI / 2)]} fontSize={3} color="white" rotation={[0, - Math.PI / 2, 0]}>東</Text>
      <Text position={[50 * Math.sin(Math.PI / 4), 3, 50 * Math.cos(Math.PI / 4)]} fontSize={3} color="white" rotation={[0, - Math.PI * 3 / 4, 0]}>南東</Text>
      <Text position={[50 * Math.sin(0), 3, 50 * Math.cos(0)]} fontSize={3} color="white" rotation={[0, Math.PI, 0]}>南</Text>
      <Text position={[50 * Math.sin(- Math.PI / 4), 3, 50 * Math.cos(- Math.PI / 4)]} fontSize={3} color="white" rotation={[0, Math.PI * 3 / 4, 0]}>南西</Text>
      <Text position={[50 * Math.sin(- Math.PI / 2), 3, 50 * Math.cos(- Math.PI / 2)]} fontSize={3} color="white" rotation={[0, Math.PI / 2, 0]}>西</Text>
      <Text position={[50 * Math.sin(- Math.PI * 3 / 4), 3, 50 * Math.cos(Math.PI * 3 / 4)]} fontSize={3} color="white" rotation={[0, Math.PI / 4, 0]}>北西</Text>

      {/* 現在時刻の衛星たちを描画 */}
      {currentPositions.map((pos) => (
        <SatellitePoint key={pos.international_designator} pos={pos} />
      ))}
    </Canvas>
  );
}
