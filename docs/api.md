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

#### `green_areas(radius=None)`

Parks, gardens, nature reserves, playgrounds, forests, woodlands.

#### `water(radius=None)`

Rivers, lakes, ponds, reservoirs, streams, canals.

#### `nuisances(radius=None)`

Power lines, transformers, industrial zones, factories.

**Raises:** `NothingFoundError`, `OverpassError`, `OverpassTimeoutError`, `OverpassRateLimitError`, `OSRMError`, `OSRMTimeoutError`

#### `climate() -> Climate`

Historical climate data (last 365 days). Uses Open-Meteo Archive API — no API key needed.

**Raises:** `OpenMeteoError`

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

## Climate

Pydantic `BaseModel` returned by `climate()`.

| Field | Type | Description |
|-------|------|-------------|
| `avg_temp` | `float \| None` | Average daily temperature (°C) |
| `max_temp` | `float \| None` | Highest recorded temperature (°C) |
| `min_temp` | `float \| None` | Lowest recorded temperature (°C) |
| `total_precipitation_mm` | `float \| None` | Total precipitation (mm) |
| `total_rain_mm` | `float \| None` | Total rain (mm) |
| `total_snow_cm` | `float \| None` | Total snowfall (cm) |
| `sunshine_hours` | `float \| None` | Total sunshine hours |
| `avg_wind_speed` | `float \| None` | Average daily max wind speed (km/h) |
| `max_wind_speed` | `float \| None` | Highest recorded wind speed (km/h) |
| `frost_days` | `int \| None` | Days with min temp below 0°C |
| `hot_days` | `int \| None` | Days with max temp above 30°C |
| `rainy_days` | `int \| None` | Days with rain > 0.1mm |
| `snow_days` | `int \| None` | Days with snowfall > 0cm |

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

## PlotReport

Pydantic `BaseModel` returned by `PlotReporter.report()`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `plot_id` | `str` | — | TERYT parcel ID |
| `lat` | `float` | — | Centroid latitude (WGS84) |
| `lon` | `float` | — | Centroid longitude (WGS84) |
| `radius` | `int` | — | Search radius in meters |
| `education` | `list[Place]` | `[]` | Schools, kindergartens, universities |
| `finance` | `list[Place]` | `[]` | ATMs, banks |
| `transport` | `list[Place]` | `[]` | Bus stops, stations, airports |
| `infrastructure` | `list[Place]` | `[]` | Shops, healthcare, services |
| `green_areas` | `list[Place]` | `[]` | Parks, gardens, forests |
| `water` | `list[Place]` | `[]` | Rivers, lakes, ponds |
| `nuisances` | `list[Place]` | `[]` | Power lines, industrial zones, factories |
| `air_quality` | `AirQuality \| None` | `None` | Air pollution data |
| `climate` | `Climate \| None` | `None` | Temperature, precipitation, wind (last 365 days) |
| `sunlight` | `SunInfo \| None` | `None` | Sun position and daylight |

## PlotReporter

```python
PlotReporter(analyzer)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `analyzer` | `PlotAnalyzer` | Analyzer to collect data from |

### Methods

#### `report(for_date=None) -> PlotReport`

Runs all analyzer methods. Catches `NothingFoundError` per category, skips air quality if no API key.

---

## PlotVisualizer

> `from plot_finder.visualizer import PlotVisualizer` — requires `pip install plot-finder[viz]`

```python
PlotVisualizer(report, *, colors=None, plot_color="red")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report` | `PlotReport` | required | Report to visualize |
| `colors` | `dict[str, str] \| None` | `None` | Override category colours |
| `plot_color` | `str` | `"red"` | Centre marker and radius circle colour |

### Methods

#### `map() -> folium.Map`

Interactive HTML map with markers, radius circle, and layer control. Requires `folium`.

#### `image(width=800, height=600, zoom=None, marker_radius=6) -> PIL.Image.Image`

Static map image from OpenStreetMap tiles. Requires `Pillow`.

#### `save(path)`

Auto-detects by extension: `.png`/`.jpg` → static image, `.html` → interactive map.

---

## PlotAI

> `from plot_finder.ai import PlotAI` — requires `pip install plot-finder[ai]`

```python
PlotAI(report, *, api_key, model="gpt-4o-mini")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report` | `PlotReport` | required | Report to analyze |
| `api_key` | `str` | required | OpenAI API key |
| `model` | `str` | `"gpt-4o-mini"` | OpenAI model to use |

### Methods

All methods return `str`.

#### `summary()`

Natural language summary of the plot and surroundings.

#### `rate(purpose="living")`

Rate the plot 1–10 for a purpose (living / investment / farming) with explanation.

#### `advantages()`

Key advantages of this location.

#### `disadvantages()`

Key disadvantages and risks.

#### `ask(question)`

Freeform Q&A about the plot.

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
| `OpenMeteoError` | `Exception` | Open-Meteo API error |

---

[Back to README](../README.md) | [Prev: AI](ai.md) | [Next: Errors](errors.md)
