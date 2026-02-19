from datetime import datetime, time

from pydantic import BaseModel


class SunInfo(BaseModel):
    date: str
    dawn: time
    sunrise: time
    solar_noon: time
    sunset: time
    dusk: time
    daylight_hours: float
    sun_elevation: float
    sun_azimuth: float
