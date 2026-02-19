# Error Handling

All custom exceptions are importable from `plot_finder`.

---

## Exception Hierarchy

```
Exception
├── ULDKError
│   └── PlotNotFoundError
├── NothingFoundError
├── OverpassError
│   ├── OverpassTimeoutError
│   └── OverpassRateLimitError
├── OSRMError
│   └── OSRMTimeoutError
└── OpenWeatherError
    └── OpenWeatherAuthError
```

## Exceptions

| Exception | When |
|-----------|------|
| `ULDKError` | Base error for ULDK API issues |
| `PlotNotFoundError` | No parcel found for given TERYT ID or coordinates |
| `NothingFoundError` | No places found within the given radius |
| `OverpassError` | Overpass API (OpenStreetMap) request failed |
| `OverpassTimeoutError` | Overpass API timed out — server is busy |
| `OverpassRateLimitError` | Overpass API rate limit exceeded (HTTP 429) |
| `OSRMError` | OSRM routing request failed |
| `OSRMTimeoutError` | OSRM request timed out |
| `OpenWeatherError` | OpenWeatherMap API request failed |
| `OpenWeatherAuthError` | Missing or invalid OpenWeatherMap API key |

## Usage

### Handling plot search errors

```python
from plot_finder import Plot, PlotNotFoundError

try:
    plot = Plot(plot_id="000000_0.0000.0000")
except PlotNotFoundError:
    print("Parcel not found")
```

### Handling analyzer errors

```python
from plot_finder import (
    Plot,
    PlotAnalyzer,
    NothingFoundError,
    OverpassTimeoutError,
    OverpassRateLimitError,
    OSRMError,
)

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

try:
    places = analyzer.education()
except NothingFoundError:
    print("No schools nearby — try a larger radius")
except OverpassTimeoutError:
    print("OpenStreetMap server is busy — try again later")
except OverpassRateLimitError:
    print("Too many requests — wait a moment")
except OSRMError:
    print("Routing service unavailable")
```

### Catch all Overpass errors

```python
from plot_finder import OverpassError

try:
    places = analyzer.transport()
except OverpassError as e:
    # Catches OverpassTimeoutError and OverpassRateLimitError too
    print(f"OpenStreetMap error: {e}")
```

---

[Back to README](../README.md) | [Prev: Place](place.md) | [Next: API Reference](api.md)
