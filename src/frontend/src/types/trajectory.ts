// src/types/trajectory.ts
export interface Position {
  international_designator: string;
  az: number;
  alt: number;
}

export interface Trajectory {
  timestamp: string;
  positions: Position[];
}

export interface TrajectoryResponse {
  trajectories: Trajectory[];
}
