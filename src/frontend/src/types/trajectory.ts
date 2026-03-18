// src/types/trajectory.ts
export interface SatPosition {
  international_designator: string;
  az: number;
  alt: number;
}

export interface Trajectory {
  timestamp: string;
  positions: SatPosition[];
}

export interface TrajectoryResponse {
  trajectories: Trajectory[];
}
