# Air Quality

Get real-time air pollution data for the plot location using the [OpenWeatherMap Air Pollution API](https://openweathermap.org/api/air-pollution).

> Requires a free API key from [openweathermap.org](https://openweathermap.org/api).

---

## Setup

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, openweather_api_key="your_key_here")
```

## Usage

```python
air = analyzer.air_quality()

print(air.aqi)        # 1-5
print(air.aqi_label)  # Good / Fair / Moderate / Poor / Very Poor
print(air.pm2_5)      # PM2.5 (ug/m3)
print(air.pm10)       # PM10 (ug/m3)
print(air.co)         # Carbon monoxide (ug/m3)
print(air.no2)        # Nitrogen dioxide (ug/m3)
print(air.o3)         # Ozone (ug/m3)
print(air.so2)        # Sulphur dioxide (ug/m3)
```

## AirQuality Fields

| Field | Type | Description |
|-------|------|-------------|
| `aqi` | `int` | Air Quality Index (1-5) |
| `aqi_label` | `str` | Human-readable label |
| `co` | `float` | Carbon monoxide (ug/m3) |
| `no` | `float` | Nitrogen monoxide (ug/m3) |
| `no2` | `float` | Nitrogen dioxide (ug/m3) |
| `o3` | `float` | Ozone (ug/m3) |
| `so2` | `float` | Sulphur dioxide (ug/m3) |
| `pm2_5` | `float` | Fine particulate matter (ug/m3) |
| `pm10` | `float` | Coarse particulate matter (ug/m3) |
| `nh3` | `float` | Ammonia (ug/m3) |

## AQI Scale

| AQI | Label | Description |
|-----|-------|-------------|
| 1 | Good | Air quality is satisfactory |
| 2 | Fair | Acceptable quality |
| 3 | Moderate | Sensitive groups may be affected |
| 4 | Poor | Everyone may experience effects |
| 5 | Very Poor | Health alert |

## Error Handling

```python
from plot_finder import OpenWeatherAuthError, OpenWeatherError

try:
    air = analyzer.air_quality()
except OpenWeatherAuthError:
    print("Invalid or missing API key")
except OpenWeatherError:
    print("OpenWeatherMap request failed")
```

## Getting an API Key

1. Register at [openweathermap.org](https://home.openweathermap.org/users/sign_up)
2. Go to [API Keys](https://home.openweathermap.org/api_keys)
3. Copy your key and pass it to `PlotAnalyzer`

The free tier allows 1,000 calls/day.

---
