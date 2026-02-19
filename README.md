# plot-finder

> Python library to find Polish land parcels and analyze their surroundings.

Query the [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) API to get parcel data by TERYT ID or coordinates, then analyze nearby infrastructure using OpenStreetMap.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Plot](#plot)
  - [Search by TERYT ID](#search-by-teryt-id)
  - [Search by Coordinates](#search-by-coordinates)
  - [Coordinate Systems](#coordinate-systems)
  - [Fields](#fields)
- [PlotAnalyzer](#plotanalyzer)
  - [Education](#education)
  - [Finance](#finance)
  - [Transport](#transport)
- [Place](#place)
- [Error Handling](#error-handling)
- [API Reference](#api-reference)
- [License](#license)

---

## Installation

```bash
pip install plot-finder
```

### Requirements

- Python 3.10+
- Dependencies: `pydantic`, `httpx`, `shapely`, `pyproj`

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer

# Find a parcel by TERYT ID
plot = Plot(plot="141201_1.0001.6509")
print(plot.voivodeship)  # mazowieckie
print(plot.centroid)     # (x, y) in EPSG:2180

# Analyze surroundings
analyzer = PlotAnalyzer(plot, radius=3000)

schools = analyzer.education()
for place in schools:
    print(f"{place.name} — {place.distance_m}m, walk {place.walk_min}min")
```

---

## Plot

The `Plot` class fetches parcel data from the ULDK API automatically on creation.

### Search by TERYT ID

```python
from plot_finder import Plot

plot = Plot(plot="141201_1.0001.6509")

print(plot.voivodeship)  # mazowieckie
print(plot.county)       # miński
print(plot.commune)      # Mińsk Mazowiecki (miasto)
print(plot.region)       # 0001
print(plot.parcel)       # 6509
print(plot.geom_wkt)     # POLYGON((...))
print(plot.geojson)      # {"type": "Polygon", "coordinates": [...]}
print(plot.centroid)     # (460149.55, 313348.56)
```

### Search by Coordinates

```python
# EPSG:2180 (default)
plot = Plot(x=460166.4, y=313380.5)

# WGS84
plot = Plot(x=21.5896, y=52.1717, srid=4326)
```

### Coordinate Systems

The `srid` parameter controls both input coordinate interpretation and output geometry format:

```python
# Input and output in EPSG:2180 (default)
plot = Plot(plot="141201_1.0001.6509")

# Input and output in WGS84
plot = Plot(plot="141201_1.0001.6509", srid=4326)
print(plot.geojson)  # coordinates in WGS84
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `plot` | `str \| None` | TERYT parcel ID |
| `x`, `y` | `float \| None` | Search coordinates |
| `srid` | `int` | Coordinate system (default: `2180`) |
| `voivodeship` | `str \| None` | Voivodeship (wojewodztwo) |
| `county` | `str \| None` | County (powiat) |
| `commune` | `str \| None` | Commune (gmina) |
| `region` | `str \| None` | Region (obreb) |
| `parcel` | `str \| None` | Parcel number |
| `geom_wkt` | `str \| None` | Geometry as WKT |
| `geom_extent` | `str \| None` | Bounding box |
| `geojson` | `dict \| None` | Geometry as GeoJSON (computed) |
| `centroid` | `tuple[float, float] \| None` | Center point `(x, y)` (computed) |
| `datasource` | `str \| None` | Data source identifier |

---

## PlotAnalyzer

Analyzes the surroundings of a `Plot` using [OpenStreetMap](https://www.openstreetmap.org/) data (via Overpass API) and real road routing (via [OSRM](https://project-osrm.org/)).

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=2000)  # default radius: 1000m
```

> Each method accepts an optional `radius` parameter to override the default.

### Education

Find schools, kindergartens, universities, and colleges:

```python
places = analyzer.education()
# or with custom radius
places = analyzer.education(radius=5000)

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

**Kinds:** `school`, `kindergarten`, `university`, `college`

### Finance

Find ATMs and banks:

```python
places = analyzer.finance()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

**Kinds:** `atm`, `bank`

### Transport

Find bus stops, tram stops, train stations, and airports:

```python
places = analyzer.transport()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

**Kinds:** `bus_stop`, `bus_station`, `tram_stop`, `station`, `halt`, `ferry_terminal`, `aerodrome`

---

## Place

Each result is a `Place` object (Pydantic model) with travel time estimates:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str \| None` | Place name from OSM |
| `kind` | `str` | Type (`school`, `atm`, `bus_stop`, etc.) |
| `lat` | `float` | Latitude (WGS84) |
| `lon` | `float` | Longitude (WGS84) |
| `distance_m` | `float` | Straight-line distance in meters |
| `walk_min` | `int` | Walking time (minutes, ~5 km/h) |
| `bike_min` | `int` | Cycling time (minutes, ~15 km/h) |
| `car_min` | `int` | Driving time (minutes, via OSRM) |

> Walking and cycling times are calculated from the real road distance (OSRM). Driving time comes directly from OSRM routing.

Results are sorted by `distance_m` (closest first).

```python
place = places[0]

# Pydantic serialization
print(place.model_dump())
print(place.model_dump_json())
```

---

## Error Handling

```python
from plot_finder import (
    PlotNotFoundError,
    NothingFoundError,
    OverpassError,
    OverpassTimeoutError,
    OverpassRateLimitError,
    OSRMError,
    OSRMTimeoutError,
)
```

| Exception | When |
|-----------|------|
| `PlotNotFoundError` | ULDK API returns no parcel for given ID/coordinates |
| `NothingFoundError` | No places found within the given radius |
| `OverpassError` | Overpass API request failed |
| `OverpassTimeoutError` | Overpass API timed out (server busy) |
| `OverpassRateLimitError` | Overpass API rate limit (429) |
| `OSRMError` | OSRM routing request failed |
| `OSRMTimeoutError` | OSRM request timed out |

### Example

```python
from plot_finder import Plot, PlotAnalyzer, NothingFoundError, OverpassTimeoutError

plot = Plot(plot="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

try:
    places = analyzer.education()
except NothingFoundError:
    print("No schools nearby, try a larger radius")
except OverpassTimeoutError:
    print("OSM server is busy, try again later")
```

### Exception Hierarchy

```
Exception
├── ULDKError
│   └── PlotNotFoundError
├── NothingFoundError
├── OverpassError
│   ├── OverpassTimeoutError
│   └── OverpassRateLimitError
└── OSRMError
    └── OSRMTimeoutError
```

---

## API Reference

### `Plot(*, plot=None, x=None, y=None, srid=2180)`

Fetch parcel data from ULDK API. Provide either `plot` (TERYT ID) or both `x` and `y`.

### `PlotAnalyzer(plot, *, radius=1000)`

Create an analyzer for a `Plot`. The `radius` (meters) is the default search radius.

### `PlotAnalyzer.education(radius=None) -> list[Place]`

Search for schools, kindergartens, universities, colleges.

### `PlotAnalyzer.finance(radius=None) -> list[Place]`

Search for ATMs and banks.

### `PlotAnalyzer.transport(radius=None) -> list[Place]`

Search for bus/tram/train stops, stations, airports.

---

## License

MIT — use it however you want.
