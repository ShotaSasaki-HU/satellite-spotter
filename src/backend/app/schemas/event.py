# app/schemas/event.py
from pydantic import BaseModel

class Event(BaseModel):
    location_name: str
    start_time: str
    visibility: float
    event_type: str
    lat: float
    lon: float
    international_designators: list[str]

    class Config:
        orm_mode = True

class EventResponse(BaseModel):
    total: int
    events: list[Event]
