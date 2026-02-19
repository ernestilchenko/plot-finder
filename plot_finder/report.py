from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

from plot_finder.air import AirQuality
from plot_finder.exceptions import (
    NothingFoundError,
    OSRMError,
    OpenWeatherAuthError,
    OverpassError,
)
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
    geometry: list[list[float]] | None = None


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

        if a.plot.geom_wkt:
            data["geometry"] = self._geometry_wgs84(a.plot.geom_wkt)

        for category in ("education", "finance", "transport", "infrastructure", "parks", "water"):
            try:
                data[category] = getattr(a, category)()
            except (NothingFoundError, OverpassError, OSRMError):
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

    @staticmethod
    def _geometry_wgs84(geom_wkt: str) -> list[list[float]]:
        import shapely.wkt
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        geom = shapely.wkt.loads(geom_wkt)
        coords = geom.exterior.coords if hasattr(geom, "exterior") else []
        return [
            [lat, lon]
            for x, y in coords
            for lon, lat in [transformer.transform(x, y)]
        ]
