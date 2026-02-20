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
    golden_hour_morning: time | None = None
    golden_hour_evening: time | None = None
    shadow_length_10m: float | None = None


class SeasonalSun(BaseModel):
    summer_solstice: SunInfo
    winter_solstice: SunInfo
    spring_equinox: SunInfo
    autumn_equinox: SunInfo
