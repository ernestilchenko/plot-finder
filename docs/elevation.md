# Elevation

Get elevation above sea level, terrain slope, and aspect (compass direction the slope faces).

Uses the [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api) — free, no API key needed.

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

elev = analyzer.elevation()
print(elev.elevation_m)   # 105.0
print(elev.slope_deg)     # 2.35
print(elev.aspect)        # NE
```

---

## How It Works

The method samples 5 points — the plot centroid plus 4 cardinal directions offset by ~30 m — and fetches their elevations in a single API call. Slope and aspect are computed from finite differences.

---

## Elevation

Pydantic `BaseModel` returned by `elevation()`.

| Field | Type | Description |
|-------|------|-------------|
| `elevation_m` | `float` | Meters above sea level |
| `slope_deg` | `float \| None` | Terrain slope (degrees) |
| `aspect` | `str \| None` | Compass direction: N, NE, E, SE, S, SW, W, NW, or flat |
| `aspect_deg` | `float \| None` | Aspect in degrees (0=N, 90=E, 180=S, 270=W) |

---

## Why It Matters

- **Flooding** — low-lying plots near water are at higher risk
- **Foundation** — steep slopes require more complex foundations
- **Drainage** — flat terrain may have poor water drainage
- **Sun exposure** — south-facing slopes get more sunlight (in the northern hemisphere)
- **Agriculture** — slope and aspect affect soil moisture and crop suitability

---

## Async

```python
async with AsyncPlotAnalyzer(plot) as analyzer:
    elev = await analyzer.elevation()
```

---

## Error Handling

```python
from plot_finder import OpenMeteoError

try:
    elev = analyzer.elevation()
except OpenMeteoError:
    print("Elevation API unavailable")
```

**Raises:** `OpenMeteoError`
