# Async API

All sync classes have async counterparts for use in `asyncio` applications. The async API provides significant speedups through concurrent HTTP requests.

---

## Quick Start

```python
import asyncio
from plot_finder import create_plot_async, AsyncPlotAnalyzer, AsyncPlotReporter

async def main():
    # Create plot (async ULDK fetch)
    plot = await create_plot_async(plot_id="141201_1.0001.6509")
    print(plot.voivodeship)  # mazowieckie

    # Analyze surroundings (concurrent OSRM + Overpass)
    async with AsyncPlotAnalyzer(plot, radius=3000) as analyzer:
        schools = await analyzer.education()
        for s in schools:
            print(f"{s.name} — {s.distance_m}m")

        # Full report — all analyses run concurrently
        report = await AsyncPlotReporter(analyzer).report()
        print(report.model_dump_json())

asyncio.run(main())
```

---

## `create_plot_async`

Async factory function — replaces `Plot(...)` constructor.

```python
plot = await create_plot_async(plot_id="141201_1.0001.6509")
plot = await create_plot_async(address="Marszalkowska 1, Warszawa")
plot = await create_plot_async(x=21.0, y=52.2, srid=4326)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plot_id` | `str \| None` | `None` | TERYT parcel ID |
| `address` | `str \| None` | `None` | Street address (geocoded via Nominatim) |
| `x` | `float \| None` | `None` | X coordinate |
| `y` | `float \| None` | `None` | Y coordinate |

Returns a standard [`Plot`](plot.md) object.

---

## `AsyncPlotAnalyzer`

Async counterpart of [`PlotAnalyzer`](analyzer.md). Must be used as an async context manager.

```python
async with AsyncPlotAnalyzer(plot, radius=2000) as analyzer:
    places = await analyzer.all_places()
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `plot` | `Plot` | required | Plot to analyze |
| `radius` | `int` | `1000` | Default search radius (m) |
| `openweather_api_key` | `str \| None` | `None` | API key for air quality |

### Methods

All methods are `async` and have the same signatures and return types as `PlotAnalyzer`:

| Method | Returns | Description |
|--------|---------|-------------|
| `await all_places()` | `dict[str, list[Place]]` | All categories in one Overpass query |
| `await education()` | `list[Place]` | Schools, kindergartens, universities |
| `await finance()` | `list[Place]` | ATMs, banks |
| `await transport()` | `list[Place]` | Bus stops, stations, airports |
| `await infrastructure()` | `list[Place]` | Shops, healthcare, services |
| `await green_areas()` | `list[Place]` | Parks, gardens, forests |
| `await water()` | `list[Place]` | Rivers, lakes, ponds |
| `await nuisances()` | `list[Place]` | Power lines, industrial zones |
| `await climate()` | `Climate` | Temperature, precipitation, wind |
| `await air_quality()` | `AirQuality` | Air pollution (requires API key) |
| `await noise()` | `Noise` | Noise from GDDKiA + OSM |
| `await risks()` | `RiskReport` | Flood, seismic, soil, landslide, noise, mining |
| `await mpzp()` | `MPZP` | Local spatial plan |
| `sunlight()` | `SunInfo` | Sun data (sync — no HTTP) |
| `sunlight_seasonal()` | `SeasonalSun` | Seasonal sun data (sync — no HTTP) |

!!! note "sunlight methods are sync"

    `sunlight()` and `sunlight_seasonal()` are **not** async because they use the `astral` library locally with no HTTP calls.

---

## `AsyncPlotReporter`

Async counterpart of [`PlotReporter`](report.md). Runs all analyses concurrently via `asyncio.gather()`.

```python
async with AsyncPlotAnalyzer(plot, radius=2000) as analyzer:
    report = await AsyncPlotReporter(analyzer).report()
```

### `await report(for_date=None) -> PlotReport`

Returns the same [`PlotReport`](report.md) model as the sync version.

---

## Performance

The async API runs OSRM routing and risk checks concurrently:

| Operation | Sync | Async | Speedup |
|-----------|------|-------|---------|
| `all_places()` (30 POIs) | ~6s | ~0.5s | ~12x |
| `risks()` (5 checks) | ~1.5s | ~0.3s | ~5x |
| Full `report()` | ~15-20s | ~3-4s | ~5x |

---

## Resilience

Both sync and async APIs include:

- **Retry with exponential backoff** for all HTTP requests (rate limits, timeouts)
- **Overpass fallback servers** — automatically tries multiple mirrors if one fails
- **OSRM fallback** — haversine distance if OSRM is unavailable
- **Concurrency control** — `Semaphore(10)` prevents OSRM overload

---
