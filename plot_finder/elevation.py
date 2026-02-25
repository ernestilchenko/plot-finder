from __future__ import annotations

from pydantic import BaseModel


class Elevation(BaseModel):
    elevation_m: float
    slope_deg: float | None = None
    aspect: str | None = None
    aspect_deg: float | None = None
