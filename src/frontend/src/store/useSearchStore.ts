// src/store/useSearchStore.ts
import { create } from "zustand";

const TOKYO_STATION = { lat: 35.68126494858904, lon: 139.7670650510304 };

// 1. 脳みそが記憶する「データの型（形）」を定義
interface SearchState {
  radius: number | "";
  pinPosition: { lat: number; lon: number };
  
  // データを書き換えるためのリモコン（関数）の型
  setRadius: (radius: number | "") => void;
  setPinPosition: (pos: { lat: number; lon: number; }) => void;
}

// 2. 脳みそ（Store）を作成
// set という魔法の関数を使って，状態を更新する仕組みを作る．
export const useSearchStore = create<SearchState>((set) => ({
  // 初期値
  radius: 10,
  pinPosition: TOKYO_STATION,

  // 更新用のアクション（リモコン）
  setRadius: (newRadius) => set({ radius: newRadius }),
  setPinPosition: (newPos) => set({ pinPosition: newPos }),
}));
