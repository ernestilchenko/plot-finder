# Climate

Get historical climate data for a plot location. Uses the [Open-Meteo Archive API](https://open-meteo.com/en/docs/historical-weather-api) — **no API key needed**.

Data covers the last 365 days and is aggregated into a single `Climate` model.

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

climate = analyzer.climate()

print(f"Avg temperature: {climate.avg_temp}°C")
print(f"Max temperature: {climate.max_temp}°C")
print(f"Min temperature: {climate.min_temp}°C")
print(f"Total precipitation: {climate.total_precipitation_mm}mm")
print(f"Sunshine hours: {climate.sunshine_hours}h")
print(f"Frost days: {climate.frost_days}")
print(f"Hot days (>30°C): {climate.hot_days}")
```

---

## Climate Model

Pydantic `BaseModel` returned by `analyzer.climate()`.

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

---

## Error Handling

```python
from plot_finder import OpenMeteoError

try:
    climate = analyzer.climate()
except OpenMeteoError as e:
    print(f"Climate data unavailable: {e}")
```

| Exception | When |
|-----------|------|
| `OpenMeteoError` | Open-Meteo API request failed or timed out |

---

[Back to README](../README.md) | [Prev: Analyzer](analyzer.md) | [Next: Air Quality](air.md)
