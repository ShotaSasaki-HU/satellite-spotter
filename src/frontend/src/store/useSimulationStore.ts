// src/store/useSimulationStore.ts
import { create } from "zustand";

// 1. 脳みそが記憶する「データの型（形）」を定義
interface SimulationState {
  horizonProfile: number[];
  
  // データを書き換えるためのリモコン（関数）の型
  setHorizonProfile: (profile: number[]) => void;
}

// 2. 脳みそ（Store）を作成
// set という魔法の関数を使って，状態を更新する仕組みを作る．
export const useSimulationStore = create<SimulationState>((set) => ({
  // 初期値
  horizonProfile: [],

  // 更新用のアクション（リモコン）
  setHorizonProfile: (newProfile) => set({ horizonProfile: newProfile }),
}));
