from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

from plot_finder.air import AirQuality
from plot_finder.exceptions import NothingFoundError, OpenWeatherAuthError
from plot_finder.place import Place
from plot_finder.sun import SunInfo

if TYPE_CHECKING:
    from plot_finder.analyzer import PlotAnalyzer


class PlotReport(BaseModel):
    plot_id: str
    lat: float
    lon: float
    radius: int
    education: list[Place] = []
    finance: list[Place] = []
    transport: list[Place] = []
    infrastructure: list[Place] = []
    parks: list[Place] = []
    water: list[Place] = []
    air_quality: AirQuality | None = None
    sunlight: SunInfo | None = None


class PlotReporter:
    def __init__(self, analyzer: PlotAnalyzer) -> None:
        self._analyzer = analyzer

    def report(self, for_date: date | None = None) -> PlotReport:
        a = self._analyzer
        data: dict = {
            "plot_id": a.plot.plot_id,
            "lat": a.lat,
            "lon": a.lon,
            "radius": a.radius,
        }

        for category in ("education", "finance", "transport", "infrastructure", "parks", "water"):
            try:
                data[category] = getattr(a, category)()
            except NothingFoundError:
                pass

        try:
            data["air_quality"] = a.air_quality()
        except (OpenWeatherAuthError, Exception):
            pass

        try:
            data["sunlight"] = a.sunlight(for_date=for_date)
        except Exception:
            pass

        return PlotReport(**data)
