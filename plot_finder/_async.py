"""Async API for plot_finder.

Usage::

    import asyncio
    from plot_finder import create_plot_async, AsyncPlotAnalyzer, AsyncPlotReporter

    async def main():
        plot = await create_plot_async(plot_id="141201_1.0001.6509")
        async with AsyncPlotAnalyzer(plot, radius=3000) as a:
            places = await a.all_places()
            risks  = await a.risks()
            report = await AsyncPlotReporter(a).report()

    asyncio.run(main())
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date

import httpx

from plot_finder.air import AirQuality
from plot_finder.climate import Climate
from plot_finder.elevation import Elevation
from plot_finder.exceptions import (
    AddressNotFoundError,
    GDDKiAError,
    GeocodeError,
    GeoportalError,
    NothingFoundError,
    OpenMeteoError,
    OpenWeatherAuthError,
    OpenWeatherError,
    OverpassError,
    OverpassRateLimitError,
    OverpassTimeoutError,
    ULDKError,
)
from plot_finder.gugik import GugikEntry
from plot_finder.kuit import KUIT
from plot_finder.land_use import LandUse, _LAND_USE_NAMES
from plot_finder.mpzp import MPZP
from plot_finder.noise import Noise, NoiseSource
from plot_finder.pog import POG, PlanZone, _POG_ZONE_NAMES
from plot_finder.suikzp import SUIKZP
from plot_finder.place import Place
from plot_finder.plot import Plot, _NOMINATIM_URL, _ULDK_URL, _build_uldk_params, _parse_uldk_response
from plot_finder.report import PlotReport, PlotReporter
from plot_finder.risks import RiskInfo, RiskReport
from plot_finder.sun import SeasonalSun, SunInfo

# Reuse constants and static helpers from sync analyzer
from plot_finder.analyzer import (
    PlotAnalyzer,
    _OPEN_METEO_ELEVATION_URL,
    _OPEN_METEO_URL,
    _OPENWEATHER_URL,
    _OVERPASS_URLS,
    _PLACE_CATEGORIES,
    _VOIVODESHIP_MAP,
    _safe_float,
)

_log = logging.getLogger("plot_finder")

# -------------------------------------------------------------------------
# Async Plot factory
# -------------------------------------------------------------------------


async def create_plot_async(
    plot_id: str | None = None,
    address: str | None = None,
    x: float | None = None,
    y: float | None = None,
) -> Plot:
    """Create a Plot with async HTTP fetching.

    Same semantics as ``Plot(plot_id=...)`` but non-blocking.
    """
    srid = 2180
    async with httpx.AsyncClient() as client:
        # Geocode address if needed
        if address and not plot_id and x is None:
            try:
                resp = await client.get(
                    _NOMINATIM_URL,
                    params={"q": address, "format": "json", "limit": 1},
                    headers={"User-Agent": "plot-finder/1.0"},
                    timeout=10,
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise GeocodeError(f"Geocoding request failed: {exc}") from exc
            results = resp.json()
            if not results:
                raise AddressNotFoundError(f"No results for address: {address}")
            y = float(results[0]["lat"])
            x = float(results[0]["lon"])
            srid = 4326

        if not plot_id and x is None:
            raise ValueError("Either 'plot_id', 'address', or both 'x' and 'y' must be provided")
        if x is not None and y is None:
            raise ValueError("Both 'x' and 'y' must be provided")

        # Fetch from ULDK
        params = _build_uldk_params(plot_id, x, y, srid)
        try:
            resp = await client.get(_ULDK_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ULDKError(f"HTTP request failed: {exc}") from exc

        fields = _parse_uldk_response(resp.text, plot_id, x, y)

    # Construct Plot with all fields so model_validator skips sync fetch
    return Plot(
        plot_id=fields.get("plot_id", plot_id),
        address=address,
        x=x,
        y=y,
        srid=srid,
        voivodeship=fields.get("voivodeship"),
        county=fields.get("county"),
        commune=fields.get("commune"),
        region=fields.get("region"),
        parcel=fields.get("parcel"),
        geom_wkt=fields.get("geom_wkt"),
        geom_extent=fields.get("geom_extent"),
        datasource=fields.get("datasource"),
    )


# -------------------------------------------------------------------------
# Async retry helpers
# -------------------------------------------------------------------------


async def _async_retry_get(
    client: httpx.AsyncClient, url: str, *,
    params: dict | None = None, headers: dict | None = None,
    timeout: float = 15, retries: int = 2, backoff: float = 1.0,
) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429 and attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
                continue
            return resp
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise last_exc  # type: ignore[misc]


async def _async_retry_post(
    client: httpx.AsyncClient, url: str, *,
    data: dict | None = None, headers: dict | None = None,
    timeout: float = 30, retries: int = 2, backoff: float = 1.0,
) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = await client.post(url, data=data, headers=headers, timeout=timeout)
            if resp.status_code == 429 and attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
                continue
            return resp
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(backoff * (2 ** attempt))
    raise last_exc  # type: ignore[misc]


# -------------------------------------------------------------------------
# AsyncPlotAnalyzer
# -------------------------------------------------------------------------


class AsyncPlotAnalyzer:
    """Async counterpart to :class:`PlotAnalyzer`.

    Supports ``async with`` for automatic client cleanup::

        async with AsyncPlotAnalyzer(plot) as a:
            schools = await a.education()
    """

    def __init__(
        self,
        plot: Plot,
        *,
        radius: int = 1000,
        openweather_api_key: str | None = None,
    ) -> None:
        self.plot = plot
        self.radius = radius
        self._openweather_api_key = openweather_api_key
        self._lat, self._lon = self._compute_centroid()
        self._cache: dict = {}
        self._client = httpx.AsyncClient()

    def _compute_centroid(self) -> tuple[float, float]:
        from pyproj import Transformer
        centroid = self.plot.centroid
        if centroid is None:
            raise ValueError("Plot has no geometry — cannot compute centroid")
        x, y = centroid
        if self.plot.srid == 4326:
            return y, x
        t = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        lon, lat = t.transform(x, y)
        return lat, lon

    def _centroid_2180(self) -> tuple[float, float]:
        from pyproj import Transformer
        centroid = self.plot.centroid
        if centroid is None:
            raise ValueError("Plot has no geometry — cannot compute centroid")
        x, y = centroid
        if self.plot.srid == 2180:
            return x, y
        t = Transformer.from_crs(f"EPSG:{self.plot.srid}", "EPSG:2180", always_xy=True)
        return t.transform(x, y)

    @property
    def lat(self) -> float:
        return self._lat

    @property
    def lon(self) -> float:
        return self._lon

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncPlotAnalyzer":
        return self

    async def __aexit__(self, *args) -> None:  # type: ignore[override]
        await self.close()

    # ------------------------------------------------------------------
    # Overpass with fallback servers
    # ------------------------------------------------------------------

    async def _overpass_request(self, query: str) -> httpx.Response:
        last_exc: Exception | None = None
        for url in _OVERPASS_URLS:
            try:
                resp = await _async_retry_post(
                    self._client, url,
                    data={"data": query}, timeout=90, retries=1, backoff=2.0,
                )
                if resp.status_code == 200 and resp.text.strip():
                    return resp
                if resp.status_code == 200:
                    continue  # empty body, try next
                if resp.status_code in (429, 504):
                    continue
                if resp.status_code == 400:
                    return resp
                return resp
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_exc = exc
        if last_exc:
            raise OverpassTimeoutError(
                f"All Overpass servers failed (tried {len(_OVERPASS_URLS)})"
            ) from last_exc
        raise OverpassError("All Overpass servers failed")

    # ------------------------------------------------------------------
    # Core Overpass runner
    # ------------------------------------------------------------------

    async def _run_overpass(self, query: str) -> list[Place]:
        resp = await self._overpass_request(query)
        if resp.status_code == 429:
            raise OverpassRateLimitError("Overpass API rate limit exceeded (429)")
        if resp.status_code == 504:
            raise OverpassTimeoutError("Overpass API server timeout (504)")
        if resp.status_code != 200:
            raise OverpassError(f"Overpass API returned {resp.status_code}")

        try:
            elements = resp.json().get("elements", [])
        except Exception:
            elements = []

        results: list[Place] = []
        for el in elements:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None or lon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name")
            kind = (
                tags.get("amenity") or tags.get("shop")
                or tags.get("public_transport") or tags.get("highway")
                or tags.get("railway") or tags.get("aeroway")
                or tags.get("leisure") or tags.get("natural")
                or tags.get("water") or tags.get("waterway")
                or tags.get("landuse") or tags.get("power")
                or tags.get("man_made") or tags.get("craft")
                or "unknown"
            )
            dist = PlotAnalyzer._haversine(self._lat, self._lon, lat, lon)
            results.append(Place(
                name=name, kind=kind, lat=lat, lon=lon,
                distance_m=round(dist),
            ))

        results.sort(key=lambda p: p.distance_m)
        return results

    # ------------------------------------------------------------------
    # Place methods (cached)
    # ------------------------------------------------------------------

    async def all_places(self, radius: int | None = None) -> dict[str, list[Place]]:
        r = radius or self.radius
        key = ("all_places", r)
        if key in self._cache:
            return self._cache[key]
        query = f"""
        [out:json][timeout:60];
        (
          nwr["amenity"~"school|kindergarten|university|college|atm|bank|bus_station|pharmacy|hospital|clinic|doctors|dentist|post_office|fuel|police|fire_station|place_of_worship|restaurant|cafe|ferry_terminal"](around:{r},{self._lat},{self._lon});
          nwr["shop"~"supermarket|convenience|mall"](around:{r},{self._lat},{self._lon});
          nwr["highway"="bus_stop"](around:{r},{self._lat},{self._lon});
          nwr["public_transport"~"platform|stop_position"](around:{r},{self._lat},{self._lon});
          nwr["railway"~"tram_stop|station|halt"](around:{r},{self._lat},{self._lon});
          nwr["aeroway"="aerodrome"](around:{r},{self._lat},{self._lon});
          nwr["leisure"~"park|garden|nature_reserve|playground"](around:{r},{self._lat},{self._lon});
          nwr["landuse"~"forest|industrial|landfill|quarry"](around:{r},{self._lat},{self._lon});
          nwr["natural"~"water|wood"](around:{r},{self._lat},{self._lon});
          nwr["water"~"river|lake|pond|reservoir"](around:{r},{self._lat},{self._lon});
          nwr["waterway"~"river|stream|canal"](around:{r},{self._lat},{self._lon});
          nwr["power"~"line|transformer|plant|generator"](around:{r},{self._lat},{self._lon});
          nwr["man_made"~"works|wastewater_plant"](around:{r},{self._lat},{self._lon});
          nwr["craft"="sawmill"](around:{r},{self._lat},{self._lon});
        );
        out center;
        """
        all_results = await self._run_overpass(query)
        categories: dict[str, list[Place]] = {
            "education": [], "finance": [], "transport": [],
            "infrastructure": [], "green_areas": [], "water": [],
            "nuisances": [],
        }
        for place in all_results:
            cat = _PLACE_CATEGORIES.get(place.kind)
            if cat:
                categories[cat].append(place)
        for cat_name, places in categories.items():
            self._cache[(cat_name, r)] = places
        self._cache[key] = categories
        return categories

    async def _place_query(self, category: str, query: str, radius: int | None) -> list[Place]:
        r = radius or self.radius
        key = (category, r)
        if key in self._cache:
            return self._cache[key]
        results = await self._run_overpass(query)
        if not results:
            raise NothingFoundError(f"No {category} found within {r}m radius")
        self._cache[key] = results
        return results

    async def education(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("education", f"""
        [out:json][timeout:25];
        (nwr["amenity"="school"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="kindergarten"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="university"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="college"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def finance(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("finance", f"""
        [out:json][timeout:25];
        (nwr["amenity"="atm"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="bank"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def transport(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("transport", f"""
        [out:json][timeout:25];
        (nwr["highway"="bus_stop"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="bus_station"](around:{r},{self._lat},{self._lon});
         nwr["public_transport"="platform"](around:{r},{self._lat},{self._lon});
         nwr["public_transport"="stop_position"](around:{r},{self._lat},{self._lon});
         nwr["railway"~"tram_stop|station|halt"](around:{r},{self._lat},{self._lon});
         nwr["amenity"="ferry_terminal"](around:{r},{self._lat},{self._lon});
         nwr["aeroway"="aerodrome"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def infrastructure(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("infrastructure", f"""
        [out:json][timeout:25];
        (nwr["shop"~"supermarket|convenience|mall"](around:{r},{self._lat},{self._lon});
         nwr["amenity"~"pharmacy|hospital|clinic|doctors|dentist|post_office|fuel|police|fire_station|place_of_worship|restaurant|cafe"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def green_areas(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("green_areas", f"""
        [out:json][timeout:25];
        (nwr["leisure"~"park|garden|nature_reserve|playground"](around:{r},{self._lat},{self._lon});
         nwr["landuse"="forest"](around:{r},{self._lat},{self._lon});
         nwr["natural"="wood"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def water(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("water", f"""
        [out:json][timeout:25];
        (nwr["natural"="water"](around:{r},{self._lat},{self._lon});
         nwr["water"~"river|lake|pond|reservoir"](around:{r},{self._lat},{self._lon});
         nwr["waterway"~"river|stream|canal"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    async def nuisances(self, radius: int | None = None) -> list[Place]:
        r = radius or self.radius
        return await self._place_query("nuisances", f"""
        [out:json][timeout:25];
        (nwr["power"~"line|transformer|plant|generator"](around:{r},{self._lat},{self._lon});
         nwr["landuse"~"industrial|landfill|quarry"](around:{r},{self._lat},{self._lon});
         nwr["man_made"~"works|wastewater_plant"](around:{r},{self._lat},{self._lon});
         nwr["craft"="sawmill"](around:{r},{self._lat},{self._lon}););
        out center;""", radius)

    # ------------------------------------------------------------------
    # Climate & weather
    # ------------------------------------------------------------------

    async def climate(self) -> Climate:
        key = ("climate",)
        if key in self._cache:
            return self._cache[key]
        end = date.today()
        start = date(end.year - 1, end.month, end.day)
        params = {
            "latitude": self._lat, "longitude": self._lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,rain_sum,snowfall_sum,sunshine_duration,wind_speed_10m_max",
            "timezone": "auto",
        }
        try:
            resp = await _async_retry_get(self._client, _OPEN_METEO_URL, params=params, timeout=15)
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

        def _safe(vals: list | None) -> list[float]:
            return [v for v in (vals or []) if v is not None]

        temps_mean = _safe(daily.get("temperature_2m_mean"))
        temps_max = _safe(daily.get("temperature_2m_max"))
        temps_min = _safe(daily.get("temperature_2m_min"))
        precip = _safe(daily.get("precipitation_sum"))
        rain = _safe(daily.get("rain_sum"))
        snow = _safe(daily.get("snowfall_sum"))
        sunshine = _safe(daily.get("sunshine_duration"))
        wind = _safe(daily.get("wind_speed_10m_max"))
        result = Climate(
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
        self._cache[key] = result
        return result

    async def elevation(self) -> Elevation:
        """Get elevation, slope, and aspect for the plot location."""
        key = ("elevation",)
        if key in self._cache:
            return self._cache[key]

        from math import atan, atan2, cos, degrees, radians, sqrt as msqrt

        dlat = 30 / 111_320
        dlon = 30 / (111_320 * cos(radians(self._lat)))
        lats = [self._lat, self._lat + dlat, self._lat - dlat, self._lat, self._lat]
        lons = [self._lon, self._lon, self._lon, self._lon + dlon, self._lon - dlon]

        try:
            resp = await _async_retry_get(
                self._client, _OPEN_METEO_ELEVATION_URL,
                params={
                    "latitude": ",".join(f"{v:.6f}" for v in lats),
                    "longitude": ",".join(f"{v:.6f}" for v in lons),
                },
                timeout=10,
            )
        except httpx.TimeoutException as exc:
            raise OpenMeteoError("Open-Meteo elevation request timed out") from exc
        except httpx.HTTPError as exc:
            raise OpenMeteoError(f"Open-Meteo elevation request failed: {exc}") from exc

        if resp.status_code != 200:
            raise OpenMeteoError(f"Open-Meteo elevation returned {resp.status_code}")

        data = resp.json()
        elevations = data.get("elevation", [])
        if not elevations or len(elevations) < 5:
            raise OpenMeteoError("Open-Meteo returned incomplete elevation data")

        centre, north, south, east, west = elevations
        dz_dx = (east - west) / 60
        dz_dy = (north - south) / 60
        slope = degrees(atan(msqrt(dz_dx ** 2 + dz_dy ** 2)))

        if dz_dx == 0 and dz_dy == 0:
            aspect_deg_val = None
            aspect_label = "flat"
        else:
            raw = degrees(atan2(dz_dx, dz_dy))
            aspect_deg_val = raw % 360
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            idx = int((aspect_deg_val + 22.5) % 360 / 45)
            aspect_label = dirs[idx]

        result = Elevation(
            elevation_m=round(centre, 1),
            slope_deg=round(slope, 2),
            aspect=aspect_label,
            aspect_deg=round(aspect_deg_val, 1) if aspect_deg_val is not None else None,
        )
        self._cache[key] = result
        return result

    async def air_quality(self) -> AirQuality:
        key = ("air_quality",)
        if key in self._cache:
            return self._cache[key]
        if not self._openweather_api_key:
            raise OpenWeatherAuthError(
                "OpenWeatherMap API key is required. "
                "Get one at https://openweathermap.org/api and pass it as "
                "AsyncPlotAnalyzer(..., openweather_api_key='your_key')"
            )
        try:
            resp = await _async_retry_get(
                self._client, _OPENWEATHER_URL,
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
        c = item["components"]
        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        result = AirQuality(
            aqi=aqi, aqi_label=aqi_labels.get(aqi, "Unknown"),
            co=c["co"], no=c["no"], no2=c["no2"], o3=c["o3"],
            so2=c["so2"], pm2_5=c["pm2_5"], pm10=c["pm10"], nh3=c["nh3"],
        )
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Sunlight — no HTTP, reuse sync
    # ------------------------------------------------------------------

    def sunlight(self, for_date: date | None = None) -> SunInfo:
        key = ("sunlight", for_date or date.today())
        if key in self._cache:
            return self._cache[key]
        sync = PlotAnalyzer.__new__(PlotAnalyzer)
        sync._lat, sync._lon = self._lat, self._lon
        sync._cache = self._cache
        sync.plot = self.plot
        result = PlotAnalyzer.sunlight(sync, for_date=for_date)
        self._cache[key] = result
        return result

    def sunlight_seasonal(self) -> SeasonalSun:
        key = ("sunlight_seasonal",)
        if key in self._cache:
            return self._cache[key]
        year = date.today().year
        result = SeasonalSun(
            summer_solstice=self.sunlight(for_date=date(year, 6, 21)),
            winter_solstice=self.sunlight(for_date=date(year, 12, 21)),
            spring_equinox=self.sunlight(for_date=date(year, 3, 20)),
            autumn_equinox=self.sunlight(for_date=date(year, 9, 22)),
        )
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Noise
    # ------------------------------------------------------------------

    async def noise(self, voivodeship: str | None = None) -> Noise:
        key = ("noise",)
        if key in self._cache:
            return self._cache[key]
        voiv = voivodeship or self.plot.voivodeship
        gddkia = await self._fetch_gddkia_noise(voiv)
        if gddkia is not None:
            db = gddkia["noise_db"]
            quality, level, desc, color = PlotAnalyzer._noise_classify(db)
            result = Noise(
                noise_level_db=db, quality=quality, level=level,
                description=desc, color=color,
                sources=[NoiseSource(
                    type="Droga krajowa (GDDKiA)", name=f"Data from {gddkia['layer']}",
                    distance_km=0, impact_db=db, lat=self._lat, lon=self._lon,
                )],
                data_source="GDDKiA",
            )
            self._cache[key] = result
            return result
        result = await self._estimate_noise_from_osm()
        self._cache[key] = result
        return result

    async def _fetch_gddkia_noise(self, voivodeship: str | None) -> dict | None:
        base_url = "https://mapy.geoportal.gov.pl/wss/service/gddkia/mapaImisyjnaLDWN"
        bbox_size = 0.001
        minx, miny = self._lon - bbox_size, self._lat - bbox_size
        maxx, maxy = self._lon + bbox_size, self._lat + bbox_size
        layers: list[str] = []
        if voivodeship:
            code = _VOIVODESHIP_MAP.get(voivodeship.lower())
            if code:
                layers.append(f"Imisja_wskaznik_LDWN_{code}")
        layers.extend([
            "Imisja_wskaznik_LDWN_mazowieckie", "Imisja_wskaznik_LDWN_lodzkie",
            "Imisja_wskaznik_LDWN_malopolskie", "Imisja_wskaznik_LDWN_slaskie",
            "Imisja_wskaznik_LDWN_wielkopolskie", "Imisja_wskaznik_LDWN_dolnoslaskie",
            "Imisja_wskaznik_LDWN_pomorskie",
        ])
        try:
            for layer in layers:
                url = (
                    f"{base_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
                    f"&LAYERS={layer}&QUERY_LAYERS={layer}&INFO_FORMAT=text/plain"
                    f"&SRS=EPSG:4326&BBOX={minx},{miny},{maxx},{maxy}"
                    f"&WIDTH=101&HEIGHT=101&X=50&Y=50"
                )
                try:
                    resp = await _async_retry_get(self._client, url, timeout=10, retries=1)
                except (httpx.TimeoutException, httpx.HTTPError):
                    continue
                if resp.status_code != 200:
                    continue
                text = resp.text
                if not text.strip() or "no features" in text.lower():
                    continue
                db_match = re.search(r"(\d+)\s*(?:dB|db)", text, re.IGNORECASE)
                if db_match:
                    return {"noise_db": int(db_match.group(1)), "layer": layer}
                range_patterns = [
                    (r">?\s*75", 80), (r"70\s*-\s*75", 72), (r"65\s*-\s*70", 67),
                    (r"60\s*-\s*65", 62), (r"55\s*-\s*60", 57), (r"50\s*-\s*55", 52),
                    (r"45\s*-\s*50", 47), (r"<?\s*45", 42),
                ]
                for pattern, db_value in range_patterns:
                    if re.search(pattern, text):
                        return {"noise_db": db_value, "layer": layer}
        except Exception:
            pass
        return None

    async def _estimate_noise_from_osm(self) -> Noise:
        query = f"""
        [out:json][timeout:30];
        (way["highway"~"motorway|trunk|primary|secondary"](around:2000,{self._lat},{self._lon});
         way["highway"="tertiary"](around:1000,{self._lat},{self._lon});
         way["highway"="residential"](around:500,{self._lat},{self._lon});
         way["railway"~"rail|light_rail"](around:2000,{self._lat},{self._lon});
         node["aeroway"="aerodrome"](around:10000,{self._lat},{self._lon});
         way["landuse"="industrial"](around:2000,{self._lat},{self._lon}););
        out center;"""
        try:
            resp = await self._overpass_request(query)
            elements = resp.json().get("elements", []) if resp.status_code == 200 else []
        except Exception:
            elements = []
        noise_sources: list[NoiseSource] = []
        noise_level_db = 40.0
        for el in elements:
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if not el_lat or not el_lon:
                continue
            tags = el.get("tags", {})
            dist = PlotAnalyzer._haversine(self._lat, self._lon, el_lat, el_lon) / 1000
            source_type, noise_impact = None, 0.0
            hw = tags.get("highway")
            if hw == "motorway":
                source_type, noise_impact = "Autostrada", max(0, 75 - dist * 10)
            elif hw == "trunk":
                source_type, noise_impact = "Droga glowna", max(0, 70 - dist * 12)
            elif hw in ("primary", "secondary"):
                source_type, noise_impact = "Droga krajowa/wojewodzka", max(0, 65 - dist * 15)
            elif hw == "tertiary":
                source_type, noise_impact = "Droga powiatowa", max(0, 55 - dist * 20)
            elif hw == "residential":
                source_type, noise_impact = "Droga lokalna", max(0, 45 - dist * 30)
            elif tags.get("railway"):
                source_type, noise_impact = "Linia kolejowa", max(0, 70 - dist * 8)
            elif tags.get("aeroway"):
                source_type, noise_impact = "Lotnisko", max(0, 80 - dist * 3)
            elif tags.get("landuse") == "industrial":
                source_type, noise_impact = "Teren przemyslowy", max(0, 60 - dist * 10)
            if source_type and noise_impact > 5:
                noise_level_db += noise_impact
                noise_sources.append(NoiseSource(
                    type=source_type, name=tags.get("name", ""),
                    distance_km=round(dist, 2), impact_db=round(noise_impact, 1),
                    lat=el_lat, lon=el_lon,
                ))
        noise_level_db = min(noise_level_db, 85)
        noise_sources.sort(key=lambda s: s.distance_km)
        quality, level, desc, color = PlotAnalyzer._noise_classify(noise_level_db)
        return Noise(
            noise_level_db=round(noise_level_db, 1), quality=quality, level=level,
            description=desc, color=color, sources=noise_sources[:10],
            data_source="OpenStreetMap (estimated)",
        )

    # ------------------------------------------------------------------
    # Risks — concurrent checks
    # ------------------------------------------------------------------

    async def risks(self) -> RiskReport:
        key = ("risks",)
        if key in self._cache:
            return self._cache[key]
        seismic = PlotAnalyzer._check_seismic(self._lat, self._lon)
        flood, soil, landslide, noise_risk, mining = await asyncio.gather(
            self._check_flood(), self._check_soil(),
            self._check_landslide(), self._check_noise_risk(),
            self._check_mining(),
        )
        checks = [flood, seismic, soil, landslide, noise_risk, mining]
        risk_list = [r for r in checks if r.is_at_risk]
        result = RiskReport(risks=risk_list, total_risks=len(risk_list))
        self._cache[key] = result
        return result

    async def _check_flood(self) -> RiskInfo:
        query = f"""[out:json][timeout:25];
        (way["natural"="water"](around:2000,{self._lat},{self._lon});
         way["waterway"="river"](around:2000,{self._lat},{self._lon});
         way["waterway"="stream"](around:2000,{self._lat},{self._lon}););
        out geom;"""
        try:
            resp = await self._overpass_request(query)
            elements = resp.json().get("elements", []) if resp.status_code == 200 else []
        except Exception:
            return RiskInfo(risk_type="flood", name="Ryzyko powodzi", level="unknown",
                            is_at_risk=False, description="Could not check flood risk.", color="gray")
        if not elements:
            return RiskInfo(risk_type="flood", name="Ryzyko powodzi", level="low",
                            is_at_risk=False, description="No flood threats detected nearby.", color="green")
        closest = float("inf")
        for el in elements:
            for node in el.get("geometry", []):
                if "lat" in node and "lon" in node:
                    d = PlotAnalyzer._haversine(self._lat, self._lon, node["lat"], node["lon"]) / 1000
                    if d < closest:
                        closest = d
        if closest < 0.5:
            return RiskInfo(risk_type="flood", name="Ryzyko powodzi", level="high", is_at_risk=True,
                            description=f"Plot {round(closest, 2)} km from water. High flood risk.", color="red")
        if closest < 1.0:
            return RiskInfo(risk_type="flood", name="Ryzyko powodzi", level="medium", is_at_risk=True,
                            description=f"Plot {round(closest, 2)} km from water. Moderate flood risk.", color="orange")
        return RiskInfo(risk_type="flood", name="Ryzyko powodzi", level="low", is_at_risk=False,
                        description=f"Plot {round(closest, 2)} km from water. Low risk.", color="yellow")

    async def _check_soil(self) -> RiskInfo:
        query = f"""[out:json][timeout:25];
        (way["landuse"="landfill"](around:3000,{self._lat},{self._lon});
         node["amenity"="waste_disposal"](around:3000,{self._lat},{self._lon});
         way["landuse"="brownfield"](around:3000,{self._lat},{self._lon});
         node["man_made"="gasometer"](around:3000,{self._lat},{self._lon});
         way["historic"="industrial"](around:3000,{self._lat},{self._lon}););
        out center;"""
        try:
            resp = await self._overpass_request(query)
            elements = resp.json().get("elements", []) if resp.status_code == 200 else []
        except Exception:
            return RiskInfo(risk_type="soil", name="Zanieczyszczenie gleby", level="unknown",
                            is_at_risk=False, description="Could not check soil contamination.", color="gray")
        if not elements:
            return RiskInfo(risk_type="soil", name="Zanieczyszczenie gleby", level="low",
                            is_at_risk=False, description="No contamination sources detected.", color="green")
        closest = float("inf")
        for el in elements:
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if el_lat and el_lon:
                d = PlotAnalyzer._haversine(self._lat, self._lon, el_lat, el_lon) / 1000
                if d < closest:
                    closest = d
        if closest < 1.0:
            return RiskInfo(risk_type="soil", name="Zanieczyszczenie gleby", level="high", is_at_risk=True,
                            description=f"Contamination source {round(closest, 2)} km away. High risk.", color="red")
        if closest < 2.0:
            return RiskInfo(risk_type="soil", name="Zanieczyszczenie gleby", level="medium", is_at_risk=True,
                            description=f"Contamination source {round(closest, 2)} km away. Moderate risk.", color="orange")
        return RiskInfo(risk_type="soil", name="Zanieczyszczenie gleby", level="low", is_at_risk=False,
                        description=f"Contamination source {round(closest, 2)} km away. Low risk.", color="yellow")

    async def _check_landslide(self) -> RiskInfo:
        sopo_url = "https://cbdgmapa.pgi.gov.pl/arcgis/rest/services/geozagrozenia/sopo/MapServer/identify"
        buffer = 0.005
        params = {
            "f": "json",
            "geometry": json.dumps({"x": self._lon, "y": self._lat, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint", "sr": "4326", "layers": "all",
            "tolerance": "5",
            "mapExtent": f"{self._lon - buffer},{self._lat - buffer},{self._lon + buffer},{self._lat + buffer}",
            "imageDisplay": "600,550,96", "returnGeometry": "false",
        }
        try:
            resp = await _async_retry_get(self._client, sopo_url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    info = results[0].get("attributes", {})
                    layer_name = results[0].get("layerName", "")
                    is_active = "aktywn" in layer_name.lower() or info.get("AKTYWNOSC") == "aktywne"
                    if is_active:
                        return RiskInfo(risk_type="landslide", name="Ryzyko osuwisk", level="high",
                                        is_at_risk=True, description="Active landslide zone (PIG-PIB SOPO).", color="red")
                    return RiskInfo(risk_type="landslide", name="Ryzyko osuwisk", level="medium",
                                    is_at_risk=True, description="Landslide-prone area (PIG-PIB SOPO).", color="orange")
        except Exception:
            pass
        mountain_regions = [
            {"name": "Karpaty", "lat_min": 49.0, "lat_max": 50.0, "lon_min": 18.5, "lon_max": 22.9, "level": "medium"},
            {"name": "Sudety", "lat_min": 50.0, "lat_max": 50.9, "lon_min": 15.5, "lon_max": 17.0, "level": "medium"},
        ]
        for region in mountain_regions:
            if (region["lat_min"] <= self._lat <= region["lat_max"]
                    and region["lon_min"] <= self._lon <= region["lon_max"]):
                return RiskInfo(risk_type="landslide", name="Ryzyko osuwisk", level="low", is_at_risk=True,
                                description=f"Plot in {region['name']} region — verify in SOPO database.", color="yellow")
        return RiskInfo(risk_type="landslide", name="Ryzyko osuwisk", level="low",
                        is_at_risk=False, description="Low landslide risk area.", color="green")

    async def _check_noise_risk(self) -> RiskInfo:
        wms = "https://mapy.geoportal.gov.pl/wss/service/gddkia/mapaTerenyZagrozoneHalasemLDWN"
        buffer = 0.001
        bbox = f"{self._lon - buffer},{self._lat - buffer},{self._lon + buffer},{self._lat + buffer}"
        params = {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "LAYERS": "0", "QUERY_LAYERS": "0", "INFO_FORMAT": "application/json",
            "SRS": "EPSG:4326", "BBOX": bbox, "WIDTH": "101", "HEIGHT": "101", "X": "50", "Y": "50",
        }
        try:
            resp = await _async_retry_get(self._client, wms, params=params, timeout=15)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    features = data.get("features", [])
                    if features:
                        props = features[0].get("properties", {})
                        noise_db = props.get("LDWN", props.get("wartosc", props.get("Value")))
                        if noise_db is not None:
                            noise_db = float(noise_db)
                            if noise_db >= 70:
                                return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="high",
                                                is_at_risk=True, description=f"Very high noise ({noise_db} dB) — GDDKiA.", color="red")
                            if noise_db >= 60:
                                return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="medium",
                                                is_at_risk=True, description=f"Elevated noise ({noise_db} dB) — GDDKiA.", color="orange")
                            return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="low",
                                            is_at_risk=False, description=f"Acceptable noise ({noise_db} dB).", color="green")
                except (ValueError, KeyError):
                    pass
        except Exception:
            pass
        # Fallback: OSM
        query = f"""[out:json][timeout:25];
        (way["highway"~"motorway|trunk|primary"](around:500,{self._lat},{self._lon});
         way["railway"~"rail|light_rail"](around:500,{self._lat},{self._lon});
         node["aeroway"="aerodrome"](around:5000,{self._lat},{self._lon}););
        out center;"""
        try:
            resp = await self._overpass_request(query)
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                has_highway = any("highway" in e.get("tags", {}) for e in elements)
                has_railway = any("railway" in e.get("tags", {}) for e in elements)
                has_airport = any("aeroway" in e.get("tags", {}) for e in elements)
                if has_airport or (has_highway and has_railway):
                    return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="high",
                                    is_at_risk=True, description="High noise exposure — major routes nearby.", color="red")
                if has_highway or has_railway:
                    return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="medium",
                                    is_at_risk=True, description="Moderate noise — major route nearby.", color="orange")
        except Exception:
            pass
        return RiskInfo(risk_type="noise", name="Halas komunikacyjny", level="low",
                        is_at_risk=False, description="Low traffic noise.", color="green")

    async def _check_mining(self) -> RiskInfo:
        query = f"""[out:json][timeout:25];
        (way["landuse"="quarry"](around:5000,{self._lat},{self._lon});
         node["man_made"="mineshaft"](around:5000,{self._lat},{self._lon});
         node["man_made"="adit"](around:5000,{self._lat},{self._lon});
         way["man_made"="mineshaft"](around:5000,{self._lat},{self._lon});
         node["historic"="mine"](around:5000,{self._lat},{self._lon});
         way["historic"="mine"](around:5000,{self._lat},{self._lon});
         way["industrial"="mine"](around:5000,{self._lat},{self._lon}););
        out center;"""
        try:
            resp = await self._overpass_request(query)
            elements = resp.json().get("elements", []) if resp.status_code == 200 else []
        except Exception:
            return RiskInfo(risk_type="mining", name="Tereny gornicze", level="unknown",
                            is_at_risk=False, description="Could not check mining areas.", color="gray")
        if not elements:
            return RiskInfo(risk_type="mining", name="Tereny gornicze", level="low",
                            is_at_risk=False, description="Plot outside mining areas.", color="green")
        closest = float("inf")
        mining_type, mine_name = "", ""
        for el in elements:
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if el_lat and el_lon:
                d = PlotAnalyzer._haversine(self._lat, self._lon, el_lat, el_lon) / 1000
                if d < closest:
                    closest = d
                    tags = el.get("tags", {})
                    mine_name = tags.get("name", "mining object")
                    if tags.get("landuse") == "quarry":
                        mining_type = "quarry"
                    elif tags.get("industrial") == "mine":
                        mining_type = "active mine"
                    elif tags.get("historic") == "mine":
                        mining_type = "historic mine"
                    elif tags.get("man_made") in ("mineshaft", "adit"):
                        mining_type = "mineshaft"
        if closest < 1.0:
            return RiskInfo(risk_type="mining", name="Tereny gornicze", level="high", is_at_risk=True,
                            description=f"{round(closest, 2)} km — {mining_type} ({mine_name}). Possible tremors.", color="red")
        if closest < 3.0:
            return RiskInfo(risk_type="mining", name="Tereny gornicze", level="medium", is_at_risk=True,
                            description=f"{round(closest, 2)} km — {mining_type} ({mine_name}). Moderate risk.", color="orange")
        return RiskInfo(risk_type="mining", name="Tereny gornicze", level="low", is_at_risk=True,
                        description=f"{round(closest, 2)} km — {mining_type} ({mine_name}). Low risk.", color="yellow")

    # ------------------------------------------------------------------
    # MPZP
    # ------------------------------------------------------------------

    async def mpzp(self) -> MPZP:
        key = ("mpzp",)
        if key in self._cache:
            return self._cache[key]
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required for MPZP. Install: pip install plot-finder[geo]")
        try:
            x, y = self._centroid_2180()
        except ValueError:
            return MPZP()
        buf = 300
        minx, miny, maxx, maxy = x - buf, y - buf, x + buf, y + buf
        width, height = 800, 800
        pixel_x = int((x - minx) / (maxx - minx) * width)
        pixel_y = int((maxy - y) / (maxy - miny) * height)
        base_url = "https://mapy.geoportal.gov.pl/wss/ext/KrajowaIntegracjaMiejscowychPlanowZagospodarowaniaPrzestrzennego"
        url = (
            f"{base_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
            f"&LAYERS=granice,raster,wektor-str,wektor-lzb,wektor-lin,wektor-pow,wektor-pkt"
            f"&QUERY_LAYERS=granice,raster,wektor-str,wektor-lzb,wektor-lin,wektor-pow,wektor-pkt"
            f"&SRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH={width}&HEIGHT={height}&X={pixel_x}&Y={pixel_y}"
            f"&INFO_FORMAT=text/html&TRANSPARENT=TRUE&FORMAT=image/png"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://mapy.geoportal.gov.pl/",
        }
        try:
            resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise GeoportalError(f"Geoportal returned {resp.status_code}")
            html_content = resp.text
            soup = BeautifulSoup(html_content, "html.parser")
            iframe = soup.find("iframe")
            if iframe and iframe.get("src"):
                src = iframe["src"]
                if src.startswith("//"):
                    src = f"https:{src}"
                elif not src.startswith("http"):
                    src = f"https://{src}"
                iframe_resp = await _async_retry_get(self._client, src, headers=headers, timeout=15)
                if iframe_resp.status_code == 200:
                    html_content = iframe_resp.text
            result = PlotAnalyzer._parse_mpzp(html_content, BeautifulSoup)
            map_url = (
                f"{base_url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                f"&LAYERS=granice,wektor-str,wektor-lzb,wektor-lin,wektor-pow,wektor-pkt"
                f"&CRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
                f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
            )
            result.wms_url = map_url
        except ImportError:
            raise
        except Exception:
            result = MPZP()
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # SUIKZP
    # ------------------------------------------------------------------

    async def suikzp(self) -> SUIKZP:
        """Get Studium Uwarunkowan i Kierunkow Zagospodarowania Przestrzennego."""
        key = ("suikzp",)
        if key in self._cache:
            return self._cache[key]

        try:
            x, y = self._centroid_2180()
        except ValueError:
            return SUIKZP()

        buf = 300
        minx, miny = x - buf, y - buf
        maxx, maxy = x + buf, y + buf
        width, height = 800, 800
        pixel_x = int((x - minx) / (maxx - minx) * width)
        pixel_y = int((maxy - y) / (maxy - miny) * height)

        base_url = "https://mapy.geoportal.gov.pl/wss/ext/KrajowaIntegracjaStudiumKierunkowZagospodarowaniaPrzestrzennego"
        url = (
            f"{base_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
            f"&LAYERS=studium&QUERY_LAYERS=studium"
            f"&SRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH={width}&HEIGHT={height}&X={pixel_x}&Y={pixel_y}"
            f"&INFO_FORMAT=application/vnd.ogc.gml&TRANSPARENT=TRUE&FORMAT=image/png"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://mapy.geoportal.gov.pl/",
        }

        try:
            resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise GeoportalError(f"Geoportal SUIKZP returned {resp.status_code}")
            result = PlotAnalyzer._parse_suikzp(resp.text)
            map_url = (
                f"{base_url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                f"&LAYERS=studium&CRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
                f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
            )
            result.wms_url = map_url
        except Exception:
            result = SUIKZP()

        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # POG
    # ------------------------------------------------------------------

    async def pog(self) -> POG:
        """Get Plan Ogolny Gminy (adopted or projected)."""
        key = ("pog",)
        if key in self._cache:
            return self._cache[key]

        try:
            x, y = self._centroid_2180()
        except ValueError:
            return POG()

        buf = 300
        minx, miny = x - buf, y - buf
        maxx, maxy = x + buf, y + buf
        width, height = 800, 800
        pixel_x = int((x - minx) / (maxx - minx) * width)
        pixel_y = int((maxy - y) / (maxy - miny) * height)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://mapy.geoportal.gov.pl/",
        }

        # Try adopted plans first
        adopted_url = "https://mapy.geoportal.gov.pl/wss/ext/PlanyOgolneGmin"
        layers = "strefaPlanistyczna,obszarUzupelnieniaZabudowy,obszarZabSrodmiejskiej,aktPlanowaniaprzestrzennego"
        url = (
            f"{adopted_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
            f"&LAYERS={layers}&QUERY_LAYERS={layers}"
            f"&SRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH={width}&HEIGHT={height}&X={pixel_x}&Y={pixel_y}"
            f"&INFO_FORMAT=application/vnd.ogc.gml&TRANSPARENT=TRUE&FORMAT=image/png"
        )

        try:
            resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
            if resp.status_code == 200:
                result = PlotAnalyzer._parse_pog(resp.text, is_draft=False)
                if result.has_plan:
                    map_url = (
                        f"{adopted_url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                        f"&LAYERS={layers}&CRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
                        f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
                    )
                    result.wms_url = map_url
                    self._cache[key] = result
                    return result
        except Exception:
            pass

        # Fallback: projected/draft plans
        draft_url = "https://mapy.geoportal.gov.pl/wss/ext/ProjektowanePlanyOgolneGmin"
        draft_layers = "strefaPlanistyczna,obszarUzupelnieniaZabudowy,obszarZabSrodmiejskiej,aktPlanowaniaprzestrzennego"
        url = (
            f"{draft_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
            f"&LAYERS={draft_layers}&QUERY_LAYERS={draft_layers}"
            f"&SRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH={width}&HEIGHT={height}&X={pixel_x}&Y={pixel_y}"
            f"&INFO_FORMAT=application/vnd.ogc.gml&TRANSPARENT=TRUE&FORMAT=image/png"
        )

        try:
            resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
            if resp.status_code == 200:
                result = PlotAnalyzer._parse_pog(resp.text, is_draft=True)
                if result.has_plan:
                    map_url = (
                        f"{draft_url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                        f"&LAYERS={draft_layers}&CRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
                        f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
                    )
                    result.wms_url = map_url
                    self._cache[key] = result
                    return result
        except Exception:
            pass

        result = POG()
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # KUIT — underground utility infrastructure
    # ------------------------------------------------------------------

    async def kuit(self) -> KUIT:
        """Check which utility networks exist near the plot."""
        key = ("kuit",)
        if key in self._cache:
            return self._cache[key]

        try:
            x, y = self._centroid_2180()
        except ValueError:
            return KUIT()

        buf = 50
        minx, miny = x - buf, y - buf
        maxx, maxy = x + buf, y + buf
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        async def _check_layer(layer: str, field: str) -> tuple[str, bool]:
            url = (
                f"{PlotAnalyzer._KUIT_URL}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap"
                f"&LAYERS={layer}&SRS=EPSG:2180"
                f"&BBOX={minx},{miny},{maxx},{maxy}"
                f"&WIDTH=256&HEIGHT=256&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
            )
            try:
                resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
                return field, len(resp.content) > PlotAnalyzer._KUIT_EMPTY_SIZE
            except Exception:
                return field, False

        results = await asyncio.gather(
            *[_check_layer(layer, field) for layer, field in PlotAnalyzer._KUIT_LAYERS]
        )
        found = dict(results)
        has_any = any(found.values())
        all_layers = ",".join(l for l, _ in PlotAnalyzer._KUIT_LAYERS)
        wms_url = (
            f"{PlotAnalyzer._KUIT_URL}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
            f"&LAYERS={all_layers}&CRS=EPSG:2180"
            f"&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
        ) if has_any else None

        result = KUIT(has_data=has_any, wms_url=wms_url, **found)
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Land use classification
    # ------------------------------------------------------------------

    async def land_use(self) -> LandUse:
        """Get official land use classification for the plot."""
        key = ("land_use",)
        if key in self._cache:
            return self._cache[key]

        try:
            x, y = self._centroid_2180()
        except ValueError:
            return LandUse()

        buf = 300
        minx, miny = x - buf, y - buf
        maxx, maxy = x + buf, y + buf
        width, height = 800, 800
        pixel_x = int((x - minx) / (maxx - minx) * width)
        pixel_y = int((maxy - y) / (maxy - miny) * height)

        url = (
            f"{PlotAnalyzer._LAND_USE_URL}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
            f"&LAYERS=klasouzytki&QUERY_LAYERS=klasouzytki"
            f"&SRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
            f"&WIDTH={width}&HEIGHT={height}&X={pixel_x}&Y={pixel_y}"
            f"&INFO_FORMAT=text/xml&TRANSPARENT=TRUE&FORMAT=image/png"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        try:
            resp = await _async_retry_get(self._client, url, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise GeoportalError(f"Land use service returned {resp.status_code}")
            result = PlotAnalyzer._parse_land_use(resp.text)
            if result.has_data:
                map_url = (
                    f"{PlotAnalyzer._LAND_USE_URL}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                    f"&LAYERS=klasouzytki&CRS=EPSG:2180&BBOX={minx},{miny},{maxx},{maxy}"
                    f"&WIDTH=800&HEIGHT=800&FORMAT=image/png&TRANSPARENT=TRUE&STYLES="
                )
                result.wms_url = map_url
        except Exception:
            result = LandUse()

        self._cache[key] = result
        return result


# -------------------------------------------------------------------------
# Async reporter — all analyses concurrently
# -------------------------------------------------------------------------


class AsyncPlotReporter:
    """Async counterpart to :class:`PlotReporter`."""

    def __init__(self, analyzer: AsyncPlotAnalyzer) -> None:
        self._analyzer = analyzer

    async def report(self, for_date: date | None = None) -> PlotReport:
        a = self._analyzer
        data: dict = {
            "plot_id": a.plot.plot_id,
            "lat": a.lat,
            "lon": a.lon,
            "radius": a.radius,
        }

        if a.plot.geom_wkt:
            data["geometry"] = PlotReporter._geometry_wgs84(a.plot.geom_wkt)

        async def _safe(coro):
            try:
                return await coro
            except Exception:
                return None

        # Run all HTTP analyses concurrently
        (places_r, climate_r, elevation_r, noise_r, risks_r,
         mpzp_r, suikzp_r, pog_r, kuit_r, land_use_r) = await asyncio.gather(
            _safe(a.all_places()),
            _safe(a.climate()),
            _safe(a.elevation()),
            _safe(a.noise()),
            _safe(a.risks()),
            _safe(a.mpzp()),
            _safe(a.suikzp()),
            _safe(a.pog()),
            _safe(a.kuit()),
            _safe(a.land_use()),
        )

        if places_r:
            for cat in ("education", "finance", "transport", "infrastructure", "green_areas", "water", "nuisances"):
                if places_r.get(cat):
                    data[cat] = places_r[cat]

        if climate_r:
            data["climate"] = climate_r
        if elevation_r:
            data["elevation"] = elevation_r
        if noise_r:
            data["noise"] = noise_r
        if risks_r:
            data["risks"] = risks_r
        if mpzp_r:
            data["mpzp"] = mpzp_r
        if suikzp_r:
            data["suikzp"] = suikzp_r
        if pog_r:
            data["pog"] = pog_r
        if kuit_r:
            data["kuit"] = kuit_r
        if land_use_r:
            data["land_use"] = land_use_r

        # Sunlight — no HTTP
        try:
            data["sunlight"] = a.sunlight(for_date=for_date)
        except Exception:
            pass
        try:
            data["seasonal_sun"] = a.sunlight_seasonal()
        except Exception:
            pass

        # GUGiK
        try:
            data["gugik"] = a.plot.gugik()
        except Exception:
            pass

        return PlotReport(**data)
