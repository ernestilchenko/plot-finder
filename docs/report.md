# PlotReporter

Generate a full structured report for a plot in a single call. `PlotReporter` runs every [PlotAnalyzer](analyzer.md) method and collects the results into a `PlotReport` Pydantic model.

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer, PlotReporter

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=2000)

reporter = PlotReporter(analyzer)
report = reporter.report()

print(report.plot_id)                # 141201_1.0001.6509
print(len(report.education))         # 5
print(report.sunlight.daylight_hours)  # 10.31
```

---

## PlotReporter

```python
PlotReporter(analyzer)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `analyzer` | `PlotAnalyzer` | Analyzer to collect data from |

### `report(for_date=None) -> PlotReport`

Runs all analyzer methods and returns a `PlotReport`. Each category is independent — if one fails with `NothingFoundError`, it is skipped (empty list). Air quality is skipped if no API key was provided.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `for_date` | `date \| None` | `None` | Date for sunlight data (default: today) |

---

## PlotReport

Pydantic `BaseModel` with all analysis results.

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

---

## Serialization

```python
# JSON
report.model_dump_json()

# Dict
report.model_dump()

# Individual fields
for place in report.green_areas:
    print(f"{place.name} — {place.distance_m}m")
```

---

## Error Handling

`PlotReporter` catches errors per category so one failing API doesn't break the whole report:

- `NothingFoundError` → category stays `[]`
- `OpenWeatherAuthError` → `air_quality` stays `None`
- `OpenMeteoError` → `climate` stays `None`
- Any other exception in `air_quality`, `climate`, or `sunlight` → field stays `None`

If you need to know *why* a category is empty, call the analyzer method directly — it will raise the original exception.

---
