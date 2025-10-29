# app/schemas/trajectory.py
from pydantic import BaseModel

class Position(BaseModel):
    international_designator: str
    az: float
    alt: float

class Trajectory(BaseModel):
    timestamp: str
    positions: list[Position]

class TrajectoryResponse(BaseModel):
    location_name: str
    trajectories: list[Trajectory]
