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
PlotAnalyzer(plot, *, radius=1000)
```

Create an analyzer for a `Plot`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plot` | `Plot` | required | Plot to analyze |
| `radius` | `int` | `1000` | Default search radius in meters |

### Methods

All methods return `list[Place]` sorted by distance. All accept an optional `radius: int` parameter.

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

---

[Back to README](../README.md) | [Prev: Errors](errors.md)
