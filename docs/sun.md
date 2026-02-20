# Sunlight

Get sun data for the plot location — sunrise, sunset, daylight hours, golden hour, shadow length, and seasonal comparisons. Calculated locally using the [astral](https://github.com/sffjunkie/astral) library, no API calls needed.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=460166.4, y=313380.5)
analyzer = PlotAnalyzer(plot)

sun = analyzer.sunlight()

print(sun.date)                  # 2026-02-19
print(sun.sunrise)               # 05:51:10
print(sun.sunset)                # 16:09:46
print(sun.daylight_hours)        # 10.31
print(sun.golden_hour_morning)   # 06:51:10
print(sun.golden_hour_evening)   # 15:09:46
print(sun.shadow_length_10m)     # 18.5
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

## Seasonal Sun

Get sun data for all four seasonal reference dates in one call:

```python
seasonal = analyzer.sunlight_seasonal()

print(seasonal.summer_solstice.daylight_hours)     # ~16.5
print(seasonal.winter_solstice.daylight_hours)     # ~8.0
print(seasonal.winter_solstice.shadow_length_10m)  # long shadow
print(seasonal.spring_equinox.daylight_hours)      # ~12.0
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
| `golden_hour_morning` | `time \| None` | End of morning golden hour (1h after sunrise) |
| `golden_hour_evening` | `time \| None` | Start of evening golden hour (1h before sunset) |
| `shadow_length_10m` | `float \| None` | Shadow length in meters for a 10m object at solar noon |

## SeasonalSun Fields

| Field | Type | Description |
|-------|------|-------------|
| `summer_solstice` | `SunInfo` | Sun data for June 21 |
| `winter_solstice` | `SunInfo` | Sun data for December 21 |
| `spring_equinox` | `SunInfo` | Sun data for March 20 |
| `autumn_equinox` | `SunInfo` | Sun data for September 22 |

## How It Works

All calculations are done locally using astronomical formulas — no API calls, no API keys, works offline. The [astral](https://github.com/sffjunkie/astral) library computes sun positions based on latitude, longitude, and date.

Shadow length is calculated using the formula: `shadow = height / tan(elevation)` where elevation is the sun's angle at solar noon.

---
