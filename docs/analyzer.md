# PlotAnalyzer

Analyzes the surroundings of a [Plot](plot.md) using [OpenStreetMap](https://www.openstreetmap.org/) data (via Overpass API) and real road routing (via [OSRM](https://project-osrm.org/)).

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

## Parks

Find parks, gardens, playgrounds, and forests.

```python
places = analyzer.parks()

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

## How It Works

1. The plot's centroid is converted from EPSG:2180 to WGS84
2. An Overpass API query searches OpenStreetMap within the radius
3. For each result, OSRM calculates the real road distance and driving time
4. Walking and cycling times are estimated from the road distance (~5 km/h and ~15 km/h)
5. Results are sorted by straight-line distance (closest first)

---

[Back to README](../README.md) | [Prev: Plot](plot.md) | [Next: Place](place.md)
