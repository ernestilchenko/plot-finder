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
| `distance_m` | `float` | Straight-line distance in meters |
| `walk_min` | `int` | Walking time in minutes (~5 km/h) |
| `bike_min` | `int` | Cycling time in minutes (~15 km/h) |
| `car_min` | `int` | Driving time in minutes (via OSRM) |

## Travel Time

- **Driving** — real route time from [OSRM](https://project-osrm.org/) (road network routing)
- **Walking & Cycling** — calculated from the OSRM road distance at average speeds (5 km/h and 15 km/h)

> Results are always sorted by `distance_m` (closest first).

## Serialization

```python
place = places[0]

# To dict
place.model_dump()
# {'name': 'Szkoła Podstawowa nr 3', 'kind': 'school', 'lat': 50.69, 'lon': 18.44,
#  'distance_m': 850.0, 'walk_min': 13, 'bike_min': 5, 'car_min': 3}

# To JSON
place.model_dump_json()

# Access fields
print(place.name)        # Szkoła Podstawowa nr 3
print(place.walk_min)    # 13
```

## Example Output

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=460166.4, y=313380.5)
analyzer = PlotAnalyzer(plot, radius=5000)

for p in analyzer.education():
    print(f"{p.kind}: {p.name}")
    print(f"  Distance: {p.distance_m}m")
    print(f"  Walk: {p.walk_min}min | Bike: {p.bike_min}min | Car: {p.car_min}min")
```

```
school: Niepubliczna Szkoła Podstawowa w Bzinicy Starej
  Distance: 1840.0m
  Walk: 28min | Bike: 10min | Car: 6min
school: Zespól Szkolno-Przedszkolny im.M.Konopnickiej
  Distance: 3193.0m
  Walk: 59min | Bike: 20min | Car: 10min
```

---

[Back to README](../README.md) | [Prev: Sunlight](sun.md) | [Next: Report](report.md)
