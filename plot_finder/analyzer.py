from __future__ import annotations

from datetime import date, datetime
from math import asin, ceil, cos, radians, sin, sqrt

import httpx
from astral import LocationInfo
from astral.sun import elevation, azimuth, sun
from pyproj import Transformer

from plot_finder.air import AirQuality
from plot_finder.climate import Climate
from plot_finder.sun import SunInfo
from plot_finder.exceptions import (
    NothingFoundError,
    OpenMeteoError,
    OSRMError,
    OSRMTimeoutError,
    OpenWeatherAuthError,
    OpenWeatherError,
    OverpassError,
    OverpassRateLimitError,
    OverpassTimeoutError,
)
from plot_finder.place import Place
from plot_finder.plot import Plot

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OSRM_URL = "https://router.project-osrm.org/route/v1"
_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
_OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

_EPSG2180_TO_WGS84 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)


class PlotAnalyzer:
    def __init__(self, plot: Plot, *, radius: int = 1000, openweather_api_key: str | None = None) -> None:
        self.plot = plot
        self.radius = radius
        self._openweather_api_key = openweather_api_key
        self._lat, self._lon = self._centroid_wgs84()

    @property
    def lat(self) -> float:
        return self._lat

    @property
    def lon(self) -> float:
        return self._lon

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

    def infrastructure(self, radius: int | None = None) -> list[Place]:
        """Find shops, pharmacies, hospitals, post offices, fuel stations, etc."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["shop"="supermarket"](around:{r},{self._lat},{self._lon});
          nwr["shop"="convenience"](around:{r},{self._lat},{self._lon});
          nwr["shop"="mall"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="pharmacy"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="hospital"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="clinic"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="doctors"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="dentist"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="post_office"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="fuel"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="police"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="fire_station"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="place_of_worship"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="restaurant"](around:{r},{self._lat},{self._lon});
          nwr["amenity"="cafe"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No infrastructure found within {r}m radius")
        return results

    def green_areas(self, radius: int | None = None) -> list[Place]:
        """Find parks, gardens, forests, and green areas."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["leisure"="park"](around:{r},{self._lat},{self._lon});
          nwr["leisure"="garden"](around:{r},{self._lat},{self._lon});
          nwr["leisure"="nature_reserve"](around:{r},{self._lat},{self._lon});
          nwr["leisure"="playground"](around:{r},{self._lat},{self._lon});
          nwr["landuse"="forest"](around:{r},{self._lat},{self._lon});
          nwr["natural"="wood"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No parks or green areas found within {r}m radius")
        return results

    def water(self, radius: int | None = None) -> list[Place]:
        """Find rivers, lakes, ponds, and reservoirs."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["natural"="water"](around:{r},{self._lat},{self._lon});
          nwr["water"="river"](around:{r},{self._lat},{self._lon});
          nwr["water"="lake"](around:{r},{self._lat},{self._lon});
          nwr["water"="pond"](around:{r},{self._lat},{self._lon});
          nwr["water"="reservoir"](around:{r},{self._lat},{self._lon});
          nwr["waterway"="river"](around:{r},{self._lat},{self._lon});
          nwr["waterway"="stream"](around:{r},{self._lat},{self._lon});
          nwr["waterway"="canal"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No water bodies found within {r}m radius")
        return results

    def nuisances(self, radius: int | None = None) -> list[Place]:
        """Find power lines, transformers, industrial zones, and factories."""
        r = radius or self.radius
        query = f"""
        [out:json][timeout:25];
        (
          nwr["power"="line"](around:{r},{self._lat},{self._lon});
          nwr["power"="transformer"](around:{r},{self._lat},{self._lon});
          nwr["landuse"="industrial"](around:{r},{self._lat},{self._lon});
          nwr["man_made"="works"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        results = self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No nuisances found within {r}m radius")
        return results

    def climate(self) -> Climate:
        """Get climate data for the plot location (last 365 days from Open-Meteo)."""
        end = date.today()
        start = date(end.year - 1, end.month, end.day)

        params = {
            "latitude": self._lat,
            "longitude": self._lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join([
                "temperature_2m_mean",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "snowfall_sum",
                "sunshine_duration",
                "wind_speed_10m_max",
            ]),
            "timezone": "auto",
        }

        try:
            resp = httpx.get(_OPEN_METEO_URL, params=params, timeout=15)
        except httpx.TimeoutException as exc:
            raise OpenMeteoError("Open-Meteo request timed out") from exc
        except httpx.HTTPError as exc:
            raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc

        if resp.status_code != 200:
            raise OpenMeteoError(f"Open-Meteo returned {resp.status_code}")

        data = resp.json()
        if "daily" not in data:
            raise OpenMeteoError("Open-Meteo returned no daily data")

        daily = data["daily"]

        def _safe(values: list | None) -> list[float]:
            return [v for v in (values or []) if v is not None]

        temps_mean = _safe(daily.get("temperature_2m_mean"))
        temps_max = _safe(daily.get("temperature_2m_max"))
        temps_min = _safe(daily.get("temperature_2m_min"))
        precip = _safe(daily.get("precipitation_sum"))
        rain = _safe(daily.get("rain_sum"))
        snow = _safe(daily.get("snowfall_sum"))
        sunshine = _safe(daily.get("sunshine_duration"))
        wind = _safe(daily.get("wind_speed_10m_max"))

        return Climate(
            avg_temp=round(sum(temps_mean) / len(temps_mean), 1) if temps_mean else None,
            max_temp=round(max(temps_max), 1) if temps_max else None,
            min_temp=round(min(temps_min), 1) if temps_min else None,
            total_precipitation_mm=round(sum(precip), 1) if precip else None,
            total_rain_mm=round(sum(rain), 1) if rain else None,
            total_snow_cm=round(sum(snow), 1) if snow else None,
            sunshine_hours=round(sum(sunshine) / 3600, 1) if sunshine else None,
            avg_wind_speed=round(sum(wind) / len(wind), 1) if wind else None,
            max_wind_speed=round(max(wind), 1) if wind else None,
            frost_days=sum(1 for t in _safe(daily.get("temperature_2m_min")) if t < 0),
            hot_days=sum(1 for t in _safe(daily.get("temperature_2m_max")) if t > 30),
            rainy_days=sum(1 for r in _safe(daily.get("rain_sum")) if r > 0.1),
            snow_days=sum(1 for s in _safe(daily.get("snowfall_sum")) if s > 0),
        )

    def air_quality(self) -> AirQuality:
        """Get air quality at the plot location. Requires openweather_api_key."""
        if not self._openweather_api_key:
            raise OpenWeatherAuthError(
                "OpenWeatherMap API key is required. "
                "Get one at https://openweathermap.org/api and pass it as "
                "PlotAnalyzer(..., openweather_api_key='your_key')"
            )

        try:
            resp = httpx.get(
                _OPENWEATHER_URL,
                params={"lat": self._lat, "lon": self._lon, "appid": self._openweather_api_key},
                timeout=10,
            )
        except httpx.TimeoutException as exc:
            raise OpenWeatherError("OpenWeatherMap request timed out") from exc
        except httpx.HTTPError as exc:
            raise OpenWeatherError(f"OpenWeatherMap request failed: {exc}") from exc

        if resp.status_code == 401:
            raise OpenWeatherAuthError("Invalid OpenWeatherMap API key")
        if resp.status_code != 200:
            raise OpenWeatherError(f"OpenWeatherMap returned {resp.status_code}")

        data = resp.json()
        item = data["list"][0]
        aqi = item["main"]["aqi"]
        components = item["components"]

        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}

        return AirQuality(
            aqi=aqi,
            aqi_label=aqi_labels.get(aqi, "Unknown"),
            co=components["co"],
            no=components["no"],
            no2=components["no2"],
            o3=components["o3"],
            so2=components["so2"],
            pm2_5=components["pm2_5"],
            pm10=components["pm10"],
            nh3=components["nh3"],
        )

    def sunlight(self, for_date: date | None = None) -> SunInfo:
        """Get sun data (sunrise, sunset, daylight hours, etc.) for the plot location."""
        d = for_date or date.today()
        loc = LocationInfo(latitude=self._lat, longitude=self._lon)
        observer = loc.observer

        s = sun(observer, date=d)
        elev = elevation(observer, dateandtime=datetime.now(tz=s["noon"].tzinfo))
        azim = azimuth(observer, dateandtime=datetime.now(tz=s["noon"].tzinfo))

        daylight = (s["sunset"] - s["sunrise"]).total_seconds() / 3600

        return SunInfo(
            date=d.isoformat(),
            dawn=s["dawn"].time(),
            sunrise=s["sunrise"].time(),
            solar_noon=s["noon"].time(),
            sunset=s["sunset"].time(),
            dusk=s["dusk"].time(),
            daylight_hours=round(daylight, 2),
            sun_elevation=round(elev, 2),
            sun_azimuth=round(azim, 2),
        )

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
                or tags.get("shop")
                or tags.get("highway")
                or tags.get("railway")
                or tags.get("aeroway")
                or tags.get("leisure")
                or tags.get("natural")
                or tags.get("water")
                or tags.get("waterway")
                or tags.get("landuse")
                or tags.get("power")
                or tags.get("man_made")
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
