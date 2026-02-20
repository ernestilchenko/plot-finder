# Sunlight

Get sun data for the plot location — sunrise, sunset, daylight hours, and current sun position. Calculated locally using the [astral](https://github.com/sffjunkie/astral) library, no API calls needed.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=460166.4, y=313380.5)
analyzer = PlotAnalyzer(plot)

sun = analyzer.sunlight()

print(sun.date)            # 2026-02-19
print(sun.sunrise)         # 05:51:10
print(sun.sunset)          # 16:09:46
print(sun.daylight_hours)  # 10.31
print(sun.sun_elevation)   # 25.2
print(sun.sun_azimuth)     # 204.28
```

## Custom Date

```python
from datetime import date

# Summer solstice
sun = analyzer.sunlight(for_date=date(2026, 6, 21))
print(sun.daylight_hours)  # ~16.5

# Winter solstice
sun = analyzer.sunlight(for_date=date(2026, 12, 21))
print(sun.daylight_hours)  # ~8.0
```

## SunInfo Fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | Date in ISO format (YYYY-MM-DD) |
| `dawn` | `time` | Civil dawn time |
| `sunrise` | `time` | Sunrise time |
| `solar_noon` | `time` | Solar noon (sun at highest point) |
| `sunset` | `time` | Sunset time |
| `dusk` | `time` | Civil dusk time |
| `daylight_hours` | `float` | Hours of daylight |
| `sun_elevation` | `float` | Current sun elevation in degrees (0 = horizon, 90 = overhead) |
| `sun_azimuth` | `float` | Current sun azimuth in degrees (0 = North, 90 = East, 180 = South) |

## How It Works

All calculations are done locally using astronomical formulas — no API calls, no API keys, works offline. The [astral](https://github.com/sffjunkie/astral) library computes sun positions based on latitude, longitude, and date.

---
