from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from math import asin, ceil, cos, radians, sin, sqrt, tan

import httpx
from astral import LocationInfo
from astral.sun import elevation, azimuth, sun
from pyproj import Transformer

from plot_finder.air import AirQuality
from plot_finder.climate import Climate
from plot_finder.gugik import GugikEntry
from plot_finder.mpzp import MPZP
from plot_finder.noise import Noise, NoiseSource
from plot_finder.risks import RiskInfo, RiskReport
from plot_finder.sun import SeasonalSun, SunInfo
from plot_finder.exceptions import (
    GDDKiAError,
    GeoportalError,
    NothingFoundError,
    OpenMeteoError,
    OSRMError,
    OSRMTimeoutError,
    OpenWeatherAuthError,
    OpenWeatherError,
    OverpassError,
    OverpassRateLimitError,
    OverpassTimeoutError,
    SOPOError,
)
from plot_finder.place import Place
from plot_finder.plot import Plot

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_OSRM_URL = "https://router.project-osrm.org/route/v1"
_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
_OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

_EPSG2180_TO_WGS84 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)

_VOIVODESHIP_MAP = {
    'dolnośląskie': 'dolnoslaskie',
    'kujawsko-pomorskie': 'kujawsko_pomorskie',
    'lubelskie': 'lubelskie',
    'lubuskie': 'lubuskie',
    'łódzkie': 'lodzkie',
    'małopolskie': 'malopolskie',
    'mazowieckie': 'mazowieckie',
    'opolskie': 'opolskie',
    'podkarpackie': 'podkarpackie',
    'podlaskie': 'podlaskie',
    'pomorskie': 'pomorskie',
    'śląskie': 'slaskie',
    'świętokrzyskie': 'swietokrzyskie',
    'warmińsko-mazurskie': 'warminsko_mazurskie',
    'wielkopolskie': 'wielkopolskie',
    'zachodniopomorskie': 'zachodnio_pomorskie',
}


class PlotAnalyzer:
    def __init__(self, plot: Plot, *, radius: int = 1000, openweather_api_key: str | None = None) -> None:
        self.plot = plot
        self.radius = radius
        self._openweather_api_key = openweather_api_key
        self._lat, self._lon = self._centroid_wgs84()
        self._cache: dict = {}

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

    # ------------------------------------------------------------------
    # Overpass-based place methods (cached)
    # ------------------------------------------------------------------

    def education(self, radius: int | None = None) -> list[Place]:
        """Find schools, kindergartens, universities within radius (meters)."""
        r = radius or self.radius
        key = ("education", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def finance(self, radius: int | None = None) -> list[Place]:
        """Find ATMs and banks within radius (meters)."""
        r = radius or self.radius
        key = ("finance", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def transport(self, radius: int | None = None) -> list[Place]:
        """Find bus/tram/train stops, stations, and airports within radius (meters)."""
        r = radius or self.radius
        key = ("transport", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def infrastructure(self, radius: int | None = None) -> list[Place]:
        """Find shops, pharmacies, hospitals, post offices, fuel stations, etc."""
        r = radius or self.radius
        key = ("infrastructure", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def green_areas(self, radius: int | None = None) -> list[Place]:
        """Find parks, gardens, forests, and green areas."""
        r = radius or self.radius
        key = ("green_areas", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def water(self, radius: int | None = None) -> list[Place]:
        """Find rivers, lakes, ponds, and reservoirs."""
        r = radius or self.radius
        key = ("water", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    def nuisances(self, radius: int | None = None) -> list[Place]:
        """Find power lines, transformers, industrial zones, and factories."""
        r = radius or self.radius
        key = ("nuisances", r)
        if key in self._cache:
            return self._cache[key]
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
        self._cache[key] = results
        return results

    # ------------------------------------------------------------------
    # Climate & weather (cached)
    # ------------------------------------------------------------------

    def climate(self) -> Climate:
        """Get climate data for the plot location (last 365 days from Open-Meteo)."""
        key = ("climate",)
        if key in self._cache:
            return self._cache[key]

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

    def air_quality(self) -> AirQuality:
        """Get air quality at the plot location. Requires openweather_api_key."""
        key = ("air_quality",)
        if key in self._cache:
            return self._cache[key]

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

        result = AirQuality(
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
        self._cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Sunlight (cached)
    # ------------------------------------------------------------------

    def sunlight(self, for_date: date | None = None) -> SunInfo:
        """Get sun data (sunrise, sunset, daylight hours, golden hour, shadow length)."""
        d = for_date or date.today()
        key = ("sunlight", d)
        if key in self._cache:
            return self._cache[key]

        loc = LocationInfo(latitude=self._lat, longitude=self._lon)
        observer = loc.observer

        s = sun(observer, date=d)
        now = datetime.now(tz=s["noon"].tzinfo)
        elev = elevation(observer, dateandtime=now)
        azim = azimuth(observer, dateandtime=now)

        daylight = (s["sunset"] - s["sunrise"]).total_seconds() / 3600

        # Golden hour: ~first/last hour after sunrise / before sunset
        golden_morning = (s["sunrise"] + timedelta(hours=1)).time()
        golden_evening = (s["sunset"] - timedelta(hours=1)).time()

        # Shadow length for a 10m object at solar noon elevation
        noon_elev = elevation(observer, dateandtime=s["noon"])
        if noon_elev > 0:
            shadow = round(10.0 / tan(radians(noon_elev)), 2)
        else:
            shadow = None

        result = SunInfo(
            date=d.isoformat(),
            dawn=s["dawn"].time(),
            sunrise=s["sunrise"].time(),
            solar_noon=s["noon"].time(),
            sunset=s["sunset"].time(),
            dusk=s["dusk"].time(),
            daylight_hours=round(daylight, 2),
            sun_elevation=round(elev, 2),
            sun_azimuth=round(azim, 2),
            golden_hour_morning=golden_morning,
            golden_hour_evening=golden_evening,
            shadow_length_10m=shadow,
        )
        self._cache[key] = result
        return result

    def sunlight_seasonal(self) -> SeasonalSun:
        """Get sun data for all four seasonal reference dates."""
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
    # Noise (ported from utils.py)
    # ------------------------------------------------------------------

    def noise(self, voivodeship: str | None = None) -> Noise:
        """Get noise level at the plot location from GDDKiA or OSM fallback."""
        key = ("noise",)
        if key in self._cache:
            return self._cache[key]

        voiv = voivodeship or self.plot.voivodeship
        gddkia = self._fetch_gddkia_noise(voiv)
        if gddkia is not None:
            db = gddkia["noise_db"]
            quality, level, desc, color = self._noise_classify(db)
            result = Noise(
                noise_level_db=db,
                quality=quality,
                level=level,
                description=desc,
                color=color,
                sources=[NoiseSource(
                    type="Droga krajowa (GDDKiA)",
                    name=f"Dane z {gddkia['layer']}",
                    distance_km=0,
                    impact_db=db,
                    lat=self._lat,
                    lon=self._lon,
                )],
                data_source="GDDKiA",
            )
            self._cache[key] = result
            return result

        # Fallback: estimate from OSM
        result = self._estimate_noise_from_osm()
        self._cache[key] = result
        return result

    def _fetch_gddkia_noise(self, voivodeship: str | None) -> dict | None:
        base_url = "https://mapy.geoportal.gov.pl/wss/service/gddkia/mapaImisyjnaLDWN"
        bbox_size = 0.001
        minx = self._lon - bbox_size
        miny = self._lat - bbox_size
        maxx = self._lon + bbox_size
        maxy = self._lat + bbox_size

        layers_to_try: list[str] = []
        if voivodeship:
            voiv_code = _VOIVODESHIP_MAP.get(voivodeship.lower())
            if voiv_code:
                layers_to_try.append(f"Imisja_wskaznik_LDWN_{voiv_code}")

        layers_to_try.extend([
            "Imisja_wskaznik_LDWN_mazowieckie",
            "Imisja_wskaznik_LDWN_lodzkie",
            "Imisja_wskaznik_LDWN_malopolskie",
            "Imisja_wskaznik_LDWN_slaskie",
            "Imisja_wskaznik_LDWN_wielkopolskie",
            "Imisja_wskaznik_LDWN_dolnoslaskie",
            "Imisja_wskaznik_LDWN_pomorskie",
        ])

        try:
            for layer in layers_to_try:
                url = (
                    f"{base_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
                    f"&LAYERS={layer}&QUERY_LAYERS={layer}"
                    f"&INFO_FORMAT=text/plain"
                    f"&SRS=EPSG:4326"
                    f"&BBOX={minx},{miny},{maxx},{maxy}"
                    f"&WIDTH=101&HEIGHT=101&X=50&Y=50"
                )
                try:
                    resp = httpx.get(url, timeout=10)
                except httpx.HTTPError:
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

    def _estimate_noise_from_osm(self) -> Noise:
        query = f"""
        [out:json][timeout:30];
        (
          way["highway"~"motorway|trunk|primary|secondary"](around:1000,{self._lat},{self._lon});
          way["railway"~"rail|light_rail"](around:1000,{self._lat},{self._lon});
          node["aeroway"="aerodrome"](around:10000,{self._lat},{self._lon});
          way["landuse"="industrial"](around:2000,{self._lat},{self._lon});
        );
        out center;
        """
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=45)
            if resp.status_code != 200:
                raise OverpassError(f"Overpass returned {resp.status_code}")
            elements = resp.json().get("elements", [])
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
            dist = self._haversine(self._lat, self._lon, el_lat, el_lon) / 1000  # km

            source_type = None
            noise_impact = 0.0

            if tags.get("highway") == "motorway":
                source_type, noise_impact = "Autostrada", max(0, 75 - dist * 10)
            elif tags.get("highway") == "trunk":
                source_type, noise_impact = "Droga glowna", max(0, 70 - dist * 12)
            elif tags.get("highway") in ("primary", "secondary"):
                source_type, noise_impact = "Droga krajowa/wojewodzka", max(0, 65 - dist * 15)
            elif tags.get("railway"):
                source_type, noise_impact = "Linia kolejowa", max(0, 70 - dist * 8)
            elif tags.get("aeroway"):
                source_type, noise_impact = "Lotnisko", max(0, 80 - dist * 3)
            elif tags.get("landuse") == "industrial":
                source_type, noise_impact = "Teren przemyslowy", max(0, 60 - dist * 10)

            if source_type and noise_impact > 5:
                noise_level_db += noise_impact
                noise_sources.append(NoiseSource(
                    type=source_type,
                    name=tags.get("name", ""),
                    distance_km=round(dist, 2),
                    impact_db=round(noise_impact, 1),
                    lat=el_lat,
                    lon=el_lon,
                ))

        noise_level_db = min(noise_level_db, 85)
        noise_sources.sort(key=lambda s: s.distance_km)
        quality, level, desc, color = self._noise_classify(noise_level_db)

        return Noise(
            noise_level_db=round(noise_level_db, 1),
            quality=quality,
            level=level,
            description=desc,
            color=color,
            sources=noise_sources[:10],
            data_source="OpenStreetMap (szacunkowy)",
        )

    @staticmethod
    def _noise_classify(db: float) -> tuple[str, str, str, str]:
        if db < 45:
            return "Bardzo niski", "very_low", "Bardzo cicha okolica, idealna do zamieszkania.", "green"
        elif db < 55:
            return "Niski", "low", "Cicha okolica, komfortowe warunki do zycia.", "lightgreen"
        elif db < 65:
            return "Umiarkowany", "moderate", "Zauwazsalny halas, ale w granicach normy.", "yellow"
        elif db < 75:
            return "Wysoki", "high", "Podwyzszony poziom halasu, moze byc uciazliwy.", "orange"
        else:
            return "Bardzo wysoki", "very_high", "Znaczny halas, moze wplywac na komfort zycia.", "red"

    # ------------------------------------------------------------------
    # Risks (ported from utils.py)
    # ------------------------------------------------------------------

    def risks(self) -> RiskReport:
        """Check all environmental and geological risks for the plot location."""
        key = ("risks",)
        if key in self._cache:
            return self._cache[key]

        checks = [
            self._check_flood(),
            self._check_seismic(),
            self._check_soil(),
            self._check_landslide(),
            self._check_noise_risk(),
            self._check_mining(),
        ]

        risk_list = [r for r in checks if r.is_at_risk]
        result = RiskReport(risks=risk_list, total_risks=len(risk_list))
        self._cache[key] = result
        return result

    def _check_flood(self) -> RiskInfo:
        query = f"""
        [out:json][timeout:25];
        (
          way["natural"="water"](around:2000,{self._lat},{self._lon});
          way["waterway"="river"](around:2000,{self._lat},{self._lon});
          way["waterway"="stream"](around:2000,{self._lat},{self._lon});
        );
        out geom;
        """
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=30)
            if resp.status_code != 200:
                raise OverpassError(f"Overpass returned {resp.status_code}")
            elements = resp.json().get("elements", [])
        except Exception:
            return RiskInfo(
                risk_type="flood", name="Ryzyko powodzi", level="unknown",
                is_at_risk=False, description="Nie udalo sie sprawdzic ryzyka powodzi.", color="gray",
            )

        if not elements:
            return RiskInfo(
                risk_type="flood", name="Ryzyko powodzi", level="low",
                is_at_risk=False,
                description="Brak wykrytych zagrozen powodziowych w bezposrednim sasiedztwie.",
                color="green",
            )

        closest = float("inf")
        for el in elements:
            for node in el.get("geometry", []):
                if "lat" in node and "lon" in node:
                    d = self._haversine(self._lat, self._lon, node["lat"], node["lon"]) / 1000
                    if d < closest:
                        closest = d

        if closest < 0.5:
            return RiskInfo(
                risk_type="flood", name="Ryzyko powodzi", level="high", is_at_risk=True,
                description=f"Dzialka w odleglosci {round(closest, 2)} km od ciekow wodnych. Wysokie ryzyko podtopien.",
                color="red",
            )
        elif closest < 1.0:
            return RiskInfo(
                risk_type="flood", name="Ryzyko powodzi", level="medium", is_at_risk=True,
                description=f"Dzialka w odleglosci {round(closest, 2)} km od ciekow wodnych. Umiarkowane ryzyko podtopien.",
                color="orange",
            )
        return RiskInfo(
            risk_type="flood", name="Ryzyko powodzi", level="low", is_at_risk=False,
            description=f"Dzialka w odleglosci {round(closest, 2)} km od ciekow wodnych. Niskie ryzyko.",
            color="yellow",
        )

    def _check_seismic(self) -> RiskInfo:
        zones = [
            {"region": "Legnica-Glogow", "lat_min": 51.0, "lat_max": 51.5, "lon_min": 15.5, "lon_max": 16.5, "level": "medium"},
            {"region": "Gorny Slask", "lat_min": 50.0, "lat_max": 50.5, "lon_min": 18.5, "lon_max": 19.5, "level": "high"},
            {"region": "Dolny Slask", "lat_min": 50.5, "lat_max": 51.5, "lon_min": 16.0, "lon_max": 17.5, "level": "low"},
        ]
        for z in zones:
            if z["lat_min"] <= self._lat <= z["lat_max"] and z["lon_min"] <= self._lon <= z["lon_max"]:
                color = {"high": "red", "medium": "orange", "low": "yellow"}[z["level"]]
                return RiskInfo(
                    risk_type="seismic", name="Aktywnosc sejsmiczna",
                    level=z["level"], is_at_risk=True,
                    description=f"Dzialka w rejonie {z['region']} — aktywnosc sejsmiczna ({z['level']}).",
                    color=color,
                )
        return RiskInfo(
            risk_type="seismic", name="Aktywnosc sejsmiczna", level="low", is_at_risk=False,
            description="Dzialka poza glownymi strefami aktywnosci sejsmicznej.", color="green",
        )

    def _check_soil(self) -> RiskInfo:
        query = f"""
        [out:json][timeout:25];
        (
          way["landuse"="landfill"](around:3000,{self._lat},{self._lon});
          node["amenity"="waste_disposal"](around:3000,{self._lat},{self._lon});
          way["landuse"="brownfield"](around:3000,{self._lat},{self._lon});
          node["man_made"="gasometer"](around:3000,{self._lat},{self._lon});
          way["historic"="industrial"](around:3000,{self._lat},{self._lon});
        );
        out center;
        """
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=30)
            if resp.status_code != 200:
                raise OverpassError(f"Overpass returned {resp.status_code}")
            elements = resp.json().get("elements", [])
        except Exception:
            return RiskInfo(
                risk_type="soil", name="Zanieczyszczenie gleby", level="unknown",
                is_at_risk=False, description="Nie udalo sie sprawdzic ryzyka zanieczyszczenia gleby.", color="gray",
            )

        if not elements:
            return RiskInfo(
                risk_type="soil", name="Zanieczyszczenie gleby", level="low", is_at_risk=False,
                description="Brak wykrytych zrodel potencjalnego zanieczyszczenia gleby w okolicy.", color="green",
            )

        closest = float("inf")
        source_name = ""
        for el in elements:
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if el_lat and el_lon:
                d = self._haversine(self._lat, self._lon, el_lat, el_lon) / 1000
                if d < closest:
                    closest = d
                    tags = el.get("tags", {})
                    if tags.get("landuse") == "landfill":
                        source_name = "skladowiska odpadow"
                    elif tags.get("amenity") == "waste_disposal":
                        source_name = "zakladu utylizacji odpadow"
                    elif tags.get("landuse") == "brownfield":
                        source_name = "terenu poprzemyslowego"
                    else:
                        source_name = "potencjalnego zrodla zanieczyszczen"

        if closest < 1.0:
            return RiskInfo(
                risk_type="soil", name="Zanieczyszczenie gleby", level="high", is_at_risk=True,
                description=f"W odleglosci {round(closest, 2)} km od {source_name}. Wysokie ryzyko zanieczyszczenia.",
                color="red",
            )
        elif closest < 2.0:
            return RiskInfo(
                risk_type="soil", name="Zanieczyszczenie gleby", level="medium", is_at_risk=True,
                description=f"W odleglosci {round(closest, 2)} km od {source_name}. Umiarkowane ryzyko.",
                color="orange",
            )
        return RiskInfo(
            risk_type="soil", name="Zanieczyszczenie gleby", level="low", is_at_risk=False,
            description=f"W odleglosci {round(closest, 2)} km od {source_name}. Niskie ryzyko.", color="yellow",
        )

    def _check_landslide(self) -> RiskInfo:
        sopo_url = "https://cbdgmapa.pgi.gov.pl/arcgis/rest/services/geozagrozenia/sopo/MapServer/identify"
        buffer = 0.005
        params = {
            "f": "json",
            "geometry": json.dumps({"x": self._lon, "y": self._lat, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint",
            "sr": "4326",
            "layers": "all",
            "tolerance": "5",
            "mapExtent": f"{self._lon - buffer},{self._lat - buffer},{self._lon + buffer},{self._lat + buffer}",
            "imageDisplay": "600,550,96",
            "returnGeometry": "false",
        }
        try:
            resp = httpx.get(sopo_url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    info = results[0].get("attributes", {})
                    layer_name = results[0].get("layerName", "")
                    is_active = "aktywn" in layer_name.lower() or info.get("AKTYWNOSC") == "aktywne"
                    if is_active:
                        return RiskInfo(
                            risk_type="landslide", name="Ryzyko osuwisk", level="high", is_at_risk=True,
                            description="Dzialka w strefie aktywnego osuwiska wg danych PIG-PIB SOPO.",
                            color="red",
                        )
                    return RiskInfo(
                        risk_type="landslide", name="Ryzyko osuwisk", level="medium", is_at_risk=True,
                        description="Dzialka na terenie zagrozonym osuwiskami wg danych PIG-PIB SOPO.",
                        color="orange",
                    )
        except Exception:
            pass

        # Fallback: mountain region check
        mountain_regions = [
            {"name": "Karpaty", "lat_min": 49.0, "lat_max": 50.0, "lon_min": 18.5, "lon_max": 22.9, "level": "medium"},
            {"name": "Sudety", "lat_min": 50.0, "lat_max": 50.9, "lon_min": 15.5, "lon_max": 17.0, "level": "medium"},
        ]
        for region in mountain_regions:
            if (region["lat_min"] <= self._lat <= region["lat_max"]
                    and region["lon_min"] <= self._lon <= region["lon_max"]):
                return RiskInfo(
                    risk_type="landslide", name="Ryzyko osuwisk", level="low", is_at_risk=True,
                    description=f"Dzialka w rejonie {region['name']} — zalecana weryfikacja w bazie SOPO.",
                    color="yellow",
                )

        return RiskInfo(
            risk_type="landslide", name="Ryzyko osuwisk", level="low", is_at_risk=False,
            description="Dzialka na terenie o niskim ryzyku osuwisk.", color="green",
        )

    def _check_noise_risk(self) -> RiskInfo:
        gddkia_wms = "https://mapy.geoportal.gov.pl/wss/service/gddkia/mapaTerenyZagrozoneHalasemLDWN"
        buffer = 0.001
        bbox = f"{self._lon - buffer},{self._lat - buffer},{self._lon + buffer},{self._lat + buffer}"
        params = {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "LAYERS": "0", "QUERY_LAYERS": "0", "INFO_FORMAT": "application/json",
            "SRS": "EPSG:4326", "BBOX": bbox, "WIDTH": "101", "HEIGHT": "101",
            "X": "50", "Y": "50",
        }
        try:
            resp = httpx.get(gddkia_wms, params=params, timeout=15)
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
                                return RiskInfo(
                                    risk_type="noise", name="Halas komunikacyjny", level="high", is_at_risk=True,
                                    description=f"Bardzo wysoki poziom halasu ({noise_db} dB) wg map GDDKiA.", color="red",
                                )
                            elif noise_db >= 60:
                                return RiskInfo(
                                    risk_type="noise", name="Halas komunikacyjny", level="medium", is_at_risk=True,
                                    description=f"Podwyzszony poziom halasu ({noise_db} dB) wg map GDDKiA.", color="orange",
                                )
                            return RiskInfo(
                                risk_type="noise", name="Halas komunikacyjny", level="low", is_at_risk=False,
                                description=f"Akceptowalny poziom halasu ({noise_db} dB).", color="green",
                            )
                except (ValueError, KeyError):
                    pass
        except Exception:
            pass

        # Fallback: OSM
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"motorway|trunk|primary"](around:500,{self._lat},{self._lon});
          way["railway"~"rail|light_rail"](around:500,{self._lat},{self._lon});
          node["aeroway"="aerodrome"](around:5000,{self._lat},{self._lon});
        );
        out center;
        """
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=30)
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                has_highway = any("highway" in e.get("tags", {}) for e in elements)
                has_railway = any("railway" in e.get("tags", {}) for e in elements)
                has_airport = any("aeroway" in e.get("tags", {}) for e in elements)
                if has_airport or (has_highway and has_railway):
                    return RiskInfo(
                        risk_type="noise", name="Halas komunikacyjny", level="high", is_at_risk=True,
                        description="Wysokie narazenie na halas — glowne trasy w poblizu.", color="red",
                    )
                elif has_highway or has_railway:
                    return RiskInfo(
                        risk_type="noise", name="Halas komunikacyjny", level="medium", is_at_risk=True,
                        description="Umiarkowany halas — glowna trasa w poblizu.", color="orange",
                    )
        except Exception:
            pass

        return RiskInfo(
            risk_type="noise", name="Halas komunikacyjny", level="low", is_at_risk=False,
            description="Niski poziom halasu komunikacyjnego.", color="green",
        )

    def _check_mining(self) -> RiskInfo:
        query = f"""
        [out:json][timeout:25];
        (
          way["landuse"="quarry"](around:5000,{self._lat},{self._lon});
          node["man_made"="mineshaft"](around:5000,{self._lat},{self._lon});
          node["man_made"="adit"](around:5000,{self._lat},{self._lon});
          way["man_made"="mineshaft"](around:5000,{self._lat},{self._lon});
          node["historic"="mine"](around:5000,{self._lat},{self._lon});
          way["historic"="mine"](around:5000,{self._lat},{self._lon});
          way["industrial"="mine"](around:5000,{self._lat},{self._lon});
        );
        out center;
        """
        try:
            resp = httpx.post(_OVERPASS_URL, data={"data": query}, timeout=30)
            if resp.status_code != 200:
                raise OverpassError(f"Overpass returned {resp.status_code}")
            elements = resp.json().get("elements", [])
        except Exception:
            return RiskInfo(
                risk_type="mining", name="Tereny gornicze", level="unknown", is_at_risk=False,
                description="Nie udalo sie sprawdzic obszarow gorniczych.", color="gray",
            )

        if not elements:
            return RiskInfo(
                risk_type="mining", name="Tereny gornicze", level="low", is_at_risk=False,
                description="Dzialka poza obszarami gorniczymi.", color="green",
            )

        closest = float("inf")
        mining_type = ""
        mine_name = ""
        for el in elements:
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if el_lat and el_lon:
                d = self._haversine(self._lat, self._lon, el_lat, el_lon) / 1000
                if d < closest:
                    closest = d
                    tags = el.get("tags", {})
                    mine_name = tags.get("name", "obiekt gorniczy")
                    if tags.get("landuse") == "quarry":
                        mining_type = "kamieniolom"
                    elif tags.get("industrial") == "mine":
                        mining_type = "aktywna kopalnia"
                    elif tags.get("historic") == "mine":
                        mining_type = "historyczna kopalnia"
                    elif tags.get("man_made") in ("mineshaft", "adit"):
                        mining_type = "szyb gorniczy"

        if closest < 1.0:
            return RiskInfo(
                risk_type="mining", name="Tereny gornicze", level="high", is_at_risk=True,
                description=f"W odleglosci {round(closest, 2)} km — {mining_type} ({mine_name}). Mozliwe wstrzasy.",
                color="red",
            )
        elif closest < 3.0:
            return RiskInfo(
                risk_type="mining", name="Tereny gornicze", level="medium", is_at_risk=True,
                description=f"W odleglosci {round(closest, 2)} km — {mining_type} ({mine_name}). Umiarkowane ryzyko.",
                color="orange",
            )
        return RiskInfo(
            risk_type="mining", name="Tereny gornicze", level="low", is_at_risk=True,
            description=f"W odleglosci {round(closest, 2)} km — {mining_type} ({mine_name}). Niskie ryzyko.",
            color="yellow",
        )

    # ------------------------------------------------------------------
    # MPZP (ported from utils.py)
    # ------------------------------------------------------------------

    def mpzp(self) -> MPZP:
        """Get local spatial development plan (MPZP) data for the plot."""
        key = ("mpzp",)
        if key in self._cache:
            return self._cache[key]

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                "beautifulsoup4 is required for MPZP queries. "
                "Install it with: pip install plot-finder[geo]"
            )

        centroid = self.plot.centroid
        if centroid is None:
            return MPZP()

        x, y = centroid
        buf = 300
        minx, miny = x - buf, y - buf
        maxx, maxy = x + buf, y + buf
        width, height = 800, 800
        pixel_x = int((x - minx) / (maxx - minx) * width)
        pixel_y = int((maxy - y) / (maxy - miny) * height)

        base_url = "https://mapy.geoportal.gov.pl/wss/ext/KrajowaIntegracjaMiejscowychPlanowZagospodarowaniaPrzestrzennego"
        params = {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "LAYERS": "granice,raster,wektor-str,wektor-lzb,wektor-lin,wektor-pow,wektor-pkt",
            "QUERY_LAYERS": "granice,raster,wektor-str,wektor-lzb,wektor-lin,wektor-pow,wektor-pkt",
            "SRS": "EPSG:2180",
            "BBOX": f"{minx},{miny},{maxx},{maxy}",
            "WIDTH": width, "HEIGHT": height, "X": pixel_x, "Y": pixel_y,
            "INFO_FORMAT": "text/html", "TRANSPARENT": "TRUE", "FORMAT": "image/png",
        }

        url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://mapy.geoportal.gov.pl/",
        }

        try:
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                raise GeoportalError(f"Geoportal returned {resp.status_code}")
            html_content = resp.text

            # Follow iframe if present
            soup = BeautifulSoup(html_content, "html.parser")
            iframe = soup.find("iframe")
            if iframe and iframe.get("src"):
                src = iframe["src"]
                if src.startswith("//"):
                    src = f"https:{src}"
                elif not src.startswith("http"):
                    src = f"https://{src}"
                iframe_resp = httpx.get(src, headers=headers, timeout=15)
                if iframe_resp.status_code == 200:
                    html_content = iframe_resp.text

            result = self._parse_mpzp(html_content, BeautifulSoup)

            # Build WMS map URL
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

    @staticmethod
    def _parse_mpzp(html_content: str, BeautifulSoup) -> MPZP:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        if not text or "brak danych" in text.lower() or "plik nie istnieje" in text.lower() or len(text) < 50:
            return MPZP()

        zone_symbol = None
        symbol_match = re.search(r"Teren oznaczony symbolem\s*(\S+)", text)
        if symbol_match:
            zone_symbol = symbol_match.group(1)
        else:
            for b in soup.find_all("b"):
                b_text = b.get_text(strip=True)
                if b_text and re.match(r"^[A-Z]{1,3}[/-]?[A-Z0-9]*$", b_text):
                    zone_symbol = b_text
                    break

        zone_name = None
        for div in soup.find_all("div"):
            div_text = div.get_text(strip=True)
            if div_text.startswith("Tereny "):
                zone_name = div_text
                break

        plan_name = None
        plan_match = re.search(r"MPZP\s+(?:dla\s+)?(.+?)(?:Publikacja|$)", text)
        if plan_match:
            plan_name = f"MPZP {plan_match.group(1).strip()}"
        else:
            for div in soup.find_all("div"):
                div_text = div.get_text(strip=True)
                if div_text.startswith("MPZP ") and len(div_text) < 100:
                    plan_name = div_text
                    break

        resolution = None
        res_match = re.search(r"Uchwala Nr\s*([^\n<]+)", text)
        if res_match:
            resolution = f"Uchwala Nr {res_match.group(1).strip()}"

        resolution_date = None
        date_match = re.search(r"z dnia\s*(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            resolution_date = date_match.group(1)

        publication = None
        pub_match = re.search(r"Publikacja:\s*([^\n]+)", text)
        if pub_match:
            publication = pub_match.group(1).strip()

        effective_date = None
        eff_match = re.search(r"Data wejscia w zycie:\s*(\d{4}-\d{2}-\d{2})", text)
        if eff_match:
            effective_date = eff_match.group(1)

        return MPZP(
            has_plan=True,
            zone_symbol=zone_symbol,
            zone_name=zone_name,
            plan_name=plan_name,
            resolution=resolution,
            resolution_date=resolution_date,
            publication=publication,
            effective_date=effective_date,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
            try:
                road_dist, car_min = self._osrm_route(lat, lon)
            except (OSRMError, OSRMTimeoutError):
                road_dist = dist
                car_min = 0
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
