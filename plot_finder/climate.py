from __future__ import annotations

from pydantic import BaseModel


class Climate(BaseModel):
    avg_temp: float | None = None
    max_temp: float | None = None
    min_temp: float | None = None
    total_precipitation_mm: float | None = None
    total_rain_mm: float | None = None
    total_snow_cm: float | None = None
    sunshine_hours: float | None = None
    avg_wind_speed: float | None = None
    max_wind_speed: float | None = None
    frost_days: int | None = None
    hot_days: int | None = None
    rainy_days: int | None = None
    snow_days: int | None = None
