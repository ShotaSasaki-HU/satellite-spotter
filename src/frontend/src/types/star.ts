// src/types/star.ts
export interface StarPosition {
  star_name: string;
  az: number;
  alt: number;
  magnitude: number;
}

export interface StarResponse {
  timestamp: string;
  positions: StarPosition[];
}
