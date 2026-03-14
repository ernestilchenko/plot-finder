# Place

Every search method in [PlotAnalyzer](analyzer.md) returns a list of `Place` objects. `Place` is a Pydantic `BaseModel`.

---

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str \| None` | Place name from OpenStreetMap |
| `kind` | `str` | Type (`school`, `atm`, `bus_stop`, `park`, etc.) |
| `lat` | `float` | Latitude (WGS84) |
| `lon` | `float` | Longitude (WGS84) |
| `distance_m` | `float` | Straight-line distance in meters (haversine) |

> Results are always sorted by `distance_m` (closest first).

## Serialization

```python
place = places[0]

# To dict
place.model_dump()
# {'name': 'Szkoła Podstawowa nr 3', 'kind': 'school', 'lat': 50.69, 'lon': 18.44,
#  'distance_m': 850.0}

# To JSON
place.model_dump_json()

# Access fields
print(place.name)        # Szkoła Podstawowa nr 3
print(place.distance_m)  # 850.0
```

## Example Output

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=460166.4, y=313380.5)
analyzer = PlotAnalyzer(plot, radius=5000)

for p in analyzer.education():
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

```
school: Niepubliczna Szkoła Podstawowa w Bzinicy Starej — 1840.0m
school: Zespól Szkolno-Przedszkolny im.M.Konopnickiej — 3193.0m
```

---
