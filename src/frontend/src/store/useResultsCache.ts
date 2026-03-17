// src/store/useResultsCache.ts を新規作成
import { create } from "zustand";
import { Event } from "@/types/event";

interface ResultsCacheState {
  cacheKey: string; // どんな条件で検索したかのID（lat-lon-radius-source）
  events: Event[];
  total: number;
  offset: number;

  setCache: (key: string, events: Event[], total: number, offset: number) => void;
}

export const useResultsCache = create<ResultsCacheState>((set) => ({
  cacheKey: "",
  events: [],
  total: 0,
  offset: 0,

  setCache: (key, events, total, offset) => {
    set({ cacheKey: key, events, total, offset })
    console.log("キャッシュ保存:", key, events.length, total, offset); // デバッグ用
  },
}));
