# app/schemas/event.py
from pydantic import BaseModel

class Score(BaseModel):
    visibility: float
    visible_time_ratio: float
    sky_glow: float
    moon_fract_illumi: float
    rain: float
    cloud: float
    met_visibility: float

class Event(BaseModel):
    location_name: str
    start_time: str
    end_time: str
    scores: Score
    event_type: str
    lat: float
    lon: float
    international_designators: list[str]

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    total: int
    events: list[Event]
