# PlotAnalyzer

Analyzes the surroundings of a [Plot](plot.md) using [OpenStreetMap](https://www.openstreetmap.org/) data (via Overpass API).

---

## Getting Started

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=2000)  # default radius: 1000m
```

> Every method accepts an optional `radius` parameter to override the default.

---

## Education

Find schools, kindergartens, universities, and colleges.

```python
places = analyzer.education()
places = analyzer.education(radius=5000)

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `school` | Primary and secondary schools |
| `kindergarten` | Kindergartens and preschools |
| `university` | Universities |
| `college` | Colleges |

---

## Finance

Find ATMs and banks.

```python
places = analyzer.finance()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `atm` | ATMs / cash machines |
| `bank` | Bank branches |

---

## Transport

Find public transport stops, train stations, and airports.

```python
places = analyzer.transport()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `bus_stop` | Bus stops |
| `bus_station` | Bus stations |
| `tram_stop` | Tram stops |
| `station` | Train stations |
| `halt` | Small railway stops |
| `ferry_terminal` | Ferry terminals |
| `aerodrome` | Airports |

---

## Infrastructure

Find shops, healthcare, restaurants, services, and public buildings.

```python
places = analyzer.infrastructure()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `supermarket` | Supermarkets |
| `convenience` | Convenience stores |
| `mall` | Shopping malls |
| `pharmacy` | Pharmacies |
| `hospital` | Hospitals |
| `clinic` | Medical clinics |
| `doctors` | Doctor offices |
| `dentist` | Dental clinics |
| `post_office` | Post offices |
| `fuel` | Gas / fuel stations |
| `police` | Police stations |
| `fire_station` | Fire stations |
| `place_of_worship` | Churches, mosques, etc. |
| `restaurant` | Restaurants |
| `cafe` | Cafes |

---

## Green Areas

Find parks, gardens, playgrounds, and forests.

```python
places = analyzer.green_areas()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `park` | Public parks |
| `garden` | Gardens |
| `nature_reserve` | Nature reserves |
| `playground` | Playgrounds |
| `forest` | Forests |
| `wood` | Woodlands |

---

## Water

Find rivers, lakes, ponds, and other water bodies.

```python
places = analyzer.water()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `water` | Generic water body |
| `river` | Rivers |
| `lake` | Lakes |
| `pond` | Ponds |
| `reservoir` | Reservoirs |
| `stream` | Streams |
| `canal` | Canals |

---

## Nuisances

Find power lines, transformers, industrial zones, and factories.

```python
places = analyzer.nuisances()

for p in places:
    print(f"{p.kind}: {p.name} — {p.distance_m}m")
```

| Kind | Description |
|------|-------------|
| `line` | Power lines |
| `transformer` | Power transformers |
| `industrial` | Industrial zones |
| `works` | Factories and plants |

---

## Climate

Get climate data for the plot location (last 365 days). Uses the [Open-Meteo](https://open-meteo.com/) Archive API — no API key needed.

```python
from plot_finder import Climate

climate = analyzer.climate()

print(f"Avg temp: {climate.avg_temp}°C")
print(f"Frost days: {climate.frost_days}")
print(f"Sunshine: {climate.sunshine_hours}h")
print(f"Total rain: {climate.total_rain_mm}mm")
```

Returns a [`Climate`](climate.md) model. See the [Climate docs](climate.md) for all fields.

**Raises:** `OpenMeteoError`

---

## All Places (Bulk)

Fetch all categories in a single Overpass query instead of calling each method separately.

```python
places = analyzer.all_places()

for category, items in places.items():
    print(f"{category}: {len(items)} places")
    for p in items:
        print(f"  {p.name} — {p.distance_m}m")
```

Returns `dict[str, list[Place]]` with keys: `education`, `finance`, `transport`, `infrastructure`, `green_areas`, `water`, `nuisances`.

!!! tip "Async"

    For faster execution, use `AsyncPlotAnalyzer` — see [Async API](async.md).

---

## How It Works

1. The plot's centroid is converted from EPSG:2180 to WGS84
2. An Overpass API query searches OpenStreetMap within the radius
3. Haversine distance is calculated from the plot centroid to each result
4. Results are sorted by distance (closest first)

---
