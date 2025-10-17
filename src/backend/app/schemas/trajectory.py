# app/schemas/trajectory.py
from pydantic import BaseModel
from datetime import datetime

class TrajectorySummary(BaseModel):
    list_timestamp_utc: list[datetime | None] = [None, None, None]
    list_sun_alt: list[float] = [-90.0, -90.0, -90.0]
    list_sun_lit: list[bool] = [True, True, True]
