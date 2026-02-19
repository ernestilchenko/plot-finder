# API Reference

Full reference for all public classes, methods, and exceptions.

---

## Plot

```python
Plot(*, plot_id=None, x=None, y=None, srid=2180)
```

Fetch parcel data from the ULDK API. Provide either `plot` (TERYT ID) or both `x` and `y`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plot_id` | `str \| None` | `None` | TERYT parcel ID |
| `x` | `float \| None` | `None` | X coordinate |
| `y` | `float \| None` | `None` | Y coordinate |
| `srid` | `int` | `2180` | Coordinate reference system |

**Raises:** `PlotNotFoundError`, `ULDKError`

---

## PlotAnalyzer

```python
PlotAnalyzer(plot, *, radius=1000, openweather_api_key=None)
```

Create an analyzer for a `Plot`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plot` | `Plot` | required | Plot to analyze |
| `radius` | `int` | `1000` | Default search radius in meters |
| `openweather_api_key` | `str \| None` | `None` | API key for air quality data |

### Methods

All place methods return `list[Place]` sorted by distance. All accept an optional `radius: int` parameter.

#### `education(radius=None)`

Schools, kindergartens, universities, colleges.

#### `finance(radius=None)`

ATMs, banks.

#### `transport(radius=None)`

Bus stops, tram stops, train stations, airports, ferry terminals.

#### `infrastructure(radius=None)`

Supermarkets, convenience stores, malls, pharmacies, hospitals, clinics, doctors, dentists, post offices, fuel stations, police, fire stations, places of worship, restaurants, cafes.

#### `parks(radius=None)`

Parks, gardens, nature reserves, playgrounds, forests, woodlands.

#### `water(radius=None)`

Rivers, lakes, ponds, reservoirs, streams, canals.

**Raises:** `NothingFoundError`, `OverpassError`, `OverpassTimeoutError`, `OverpassRateLimitError`, `OSRMError`, `OSRMTimeoutError`

#### `air_quality() -> AirQuality`

Current air pollution data. Requires `openweather_api_key`.

**Raises:** `OpenWeatherAuthError`, `OpenWeatherError`

#### `sunlight(for_date=None) -> SunInfo`

Sun data (sunrise, sunset, daylight hours, sun position). No API key needed.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `for_date` | `date \| None` | `None` | Date to calculate for (default: today) |

---

## AirQuality

Pydantic `BaseModel` returned by `air_quality()`.

| Field | Type | Description |
|-------|------|-------------|
| `aqi` | `int` | Air Quality Index (1-5) |
| `aqi_label` | `str` | Good / Fair / Moderate / Poor / Very Poor |
| `co` | `float` | Carbon monoxide (ug/m3) |
| `no` | `float` | Nitrogen monoxide (ug/m3) |
| `no2` | `float` | Nitrogen dioxide (ug/m3) |
| `o3` | `float` | Ozone (ug/m3) |
| `so2` | `float` | Sulphur dioxide (ug/m3) |
| `pm2_5` | `float` | Fine particulate matter (ug/m3) |
| `pm10` | `float` | Coarse particulate matter (ug/m3) |
| `nh3` | `float` | Ammonia (ug/m3) |

## SunInfo

Pydantic `BaseModel` returned by `sunlight()`.

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | Date (ISO format) |
| `dawn` | `time` | Civil dawn |
| `sunrise` | `time` | Sunrise |
| `solar_noon` | `time` | Solar noon |
| `sunset` | `time` | Sunset |
| `dusk` | `time` | Civil dusk |
| `daylight_hours` | `float` | Hours of daylight |
| `sun_elevation` | `float` | Current sun elevation (degrees) |
| `sun_azimuth` | `float` | Current sun azimuth (degrees) |

---

## Place

Pydantic `BaseModel` returned by all analyzer methods.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str \| None` | Place name from OSM |
| `kind` | `str` | Type identifier |
| `lat` | `float` | Latitude (WGS84) |
| `lon` | `float` | Longitude (WGS84) |
| `distance_m` | `float` | Straight-line distance (m) |
| `walk_min` | `int` | Walking time (min) |
| `bike_min` | `int` | Cycling time (min) |
| `car_min` | `int` | Driving time (min) |

---

## Exceptions

| Exception | Parent | Description |
|-----------|--------|-------------|
| `ULDKError` | `Exception` | Base ULDK API error |
| `PlotNotFoundError` | `ULDKError` | Parcel not found |
| `NothingFoundError` | `Exception` | No results in radius |
| `OverpassError` | `Exception` | Base Overpass API error |
| `OverpassTimeoutError` | `OverpassError` | Overpass timeout |
| `OverpassRateLimitError` | `OverpassError` | Overpass rate limit (429) |
| `OSRMError` | `Exception` | Base OSRM error |
| `OSRMTimeoutError` | `OSRMError` | OSRM timeout |
| `OpenWeatherError` | `Exception` | Base OpenWeatherMap error |
| `OpenWeatherAuthError` | `OpenWeatherError` | Missing/invalid API key |

---

[Back to README](../README.md) | [Prev: Errors](errors.md)
