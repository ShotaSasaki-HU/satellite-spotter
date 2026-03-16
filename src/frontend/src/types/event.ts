// src/types/event.ts
export interface Score {
  visibility: number;
  visible_time_ratio: number;
  sky_glow: number;
  moon_fract_illumi: number;
  rain: number;
  cloud: number;
  met_visibility: number;
}

export interface Event {
  location_name: string;
  start_time: string;
  end_time: string;
  scores: Score;
  event_type: string;
  lat: number;
  lon: number;
  international_designators: string[];
  horizon_profile: number[]; // 天球シミュレータで使用
}

export interface EventResponse {
  total: number;
  events: Event[];
}
