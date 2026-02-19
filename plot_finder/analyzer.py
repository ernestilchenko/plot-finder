from __future__ import annotations

from math import asin, ceil, cos, radians, sin, sqrt

import httpx
from pyproj import Transformer

from plot_finder.exceptions import (
    NothingFoundError,
    OSRMError,
    OSRMTimeoutError,
    OverpassError,
    OverpassRateLimitError,
    OverpassTimeoutError,
)
from plot_finder.place import Place
from plot_finder.plot import Plot

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OSRM_URL = "https://router.project-osrm.org/route/v1"

_EPSG2180_TO_WGS84 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)


class PlotAnalyzer:
    def __init__(self, plot: Plot, *, radius: int = 1000) -> None:
        self.plot = plot
        self.radius = radius
        self._lat, self._lon = self._centroid_wgs84()

    def _centroid_wgs84(self) -> tuple[float, float]:
        centroid = self.plot.centroid
        if centroid is None:
            raise ValueError("Plot has no geometry — cannot compute centroid")
        x, y = centroid
        lon, lat = _EPSG2180_TO_WGS84.transform(x, y)
        return lat, lon

    def education(self, radius: int | None = None) -> list[Place]:
        """Find schools, kindergartens, universities within radius (meters)."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["amenity"="school"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="kindergarten"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="university"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="college"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No education places found within {r}m radius")
        return results

    def finance(self, radius: int | None = None) -> list[Place]:
        """Find ATMs and banks within radius (meters)."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["amenity"="atm"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="bank"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No ATMs or banks found within {r}m radius")
        return results

    def transport(self, radius: int | None = None) -> list[Place]:
        """Find bus/tram/train stops, stations, and airports within radius (meters)."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["highway"="bus_stop"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="bus_station"](around:{r},{self._lat},{self._lon});
          nwr["railway"="tram_stop"](around:{r},{self._lat},{self._lon});
          nwr["railway"="station"](around:{r},{self._lat},{self._lon});
          nwr["railway"="halt"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="ferry_terminal"](around:{r},{self._lat},{self._lon});
          nwr["aeroway"="aerodrome"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No transport stops found within {r}m radius")
        return results

    def _run_overpass(self, query: str) -> list[Place]:
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=90)
        except httpx.TimeoutException as exc:
            raise OverpassTimeoutError("Overpass API request timed out") from exc
        except httpx.HTTPError as exc:
            raise OverpassError(f"Overpass API request failed: {exc}") from exc

        if resp.status_code == 429:
            raise OverpassRateLimitError("Overpass API rate limit exceeded (429)")
        if resp.status_code == 504:
            raise OverpassTimeoutError("Overpass API server timeout (504)")
        if resp.status_code != 200:
            raise OverpassError(f"Overpass API returned {resp.status_code}")

        elements = resp.json().get("elements", [])

        results: list[Place] = []
        for el in elements:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None or lon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name")
            kind = (
                tags.get("amenity")
                or tags.get("highway")
                or tags.get("railway")
                or tags.get("aeroway")
                or "unknown"
            )
            dist = self._haversine(self._lat, self._lon, lat, lon)
            road_dist, car_min = self._osrm_route(lat, lon)
            results.append(Place(
                name=name, kind=kind, lat=lat, lon=lon,
                distance_m=round(dist),
                walk_min=ceil(road_dist / 1000 / 5.0 * 60),
                bike_min=ceil(road_dist / 1000 / 15.0 * 60),
                car_min=car_min,
            ))

        results.sort(key=lambda p: p.distance_m)
        return results

    def _osrm_route(self, dest_lat: float, dest_lon: float) -> tuple[float, int]:
        """Get road distance (meters) and driving duration (minutes) via OSRM."""
        url = (
            f"{_OSRM_URL}/driving/"
            f"{self._lon},{self._lat};{dest_lon},{dest_lat}"
        )
        try:
            resp = httpx.get(url, params={"overview": "false"}, timeout=10)
        except httpx.TimeoutException as exc:
            raise OSRMTimeoutError("OSRM request timed out") from exc
        except httpx.HTTPError as exc:
            raise OSRMError(f"OSRM request failed: {exc}") from exc

        if resp.status_code != 200:
            raise OSRMError(f"OSRM returned {resp.status_code}")

        data = resp.json()
        if data.get("code") != "Ok":
            raise OSRMError(f"OSRM error: {data.get('code')} — {data.get('message', '')}")

        routes = data.get("routes", [])
        if not routes:
            raise OSRMError("OSRM returned no routes")

        route = routes[0]
        return route["distance"], ceil(route["duration"] / 60)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 6371000 * 2 * asin(sqrt(a))
