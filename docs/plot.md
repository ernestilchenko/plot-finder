# Plot

The `Plot` class fetches parcel data from the Polish [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) API automatically on creation.

---

## Search by TERYT ID

```python
from plot_finder import Plot

plot = Plot(plot_id="141201_1.0001.6509")

print(plot.voivodeship)  # mazowieckie
print(plot.county)       # miński
print(plot.commune)      # Mińsk Mazowiecki (miasto)
print(plot.region)       # 0001
print(plot.parcel)       # 6509
print(plot.geom_wkt)     # POLYGON((...))
print(plot.geojson)      # {"type": "Polygon", "coordinates": [...]}
print(plot.centroid)     # (460149.55, 313348.56)
```

## Search by Address

```python
plot = Plot(address="ul. Nowy Świat 1, Warszawa")

print(plot.plot_id)      # TERYT ID
print(plot.voivodeship)  # mazowieckie
```

The address is geocoded to coordinates via [Nominatim](https://nominatim.openstreetmap.org/) (free, no API key required), then used to find the parcel.

## Search by Coordinates

```python
# EPSG:2180 (default Polish coordinate system)
plot = Plot(x=460166.4, y=313380.5)

# WGS84
plot = Plot(x=21.5896, y=52.1717, srid=4326)
```

## Coordinate Systems

The `srid` parameter controls both input coordinate interpretation and output geometry format:

```python
# Input and output in EPSG:2180 (default)
plot = Plot(plot_id="141201_1.0001.6509")

# Input and output in WGS84
plot = Plot(plot_id="141201_1.0001.6509", srid=4326)
print(plot.geojson)  # coordinates in WGS84
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `plot_id` | `str \| None` | TERYT parcel ID |
| `address` | `str \| None` | Street address (geocoded via Nominatim) |
| `x`, `y` | `float \| None` | Search coordinates |
| `srid` | `int` | Coordinate system (default: `2180`) |
| `voivodeship` | `str \| None` | Voivodeship (wojewodztwo) |
| `county` | `str \| None` | County (powiat) |
| `commune` | `str \| None` | Commune (gmina) |
| `region` | `str \| None` | Region (obreb) |
| `parcel` | `str \| None` | Parcel number |
| `geom_wkt` | `str \| None` | Geometry as WKT |
| `geom_extent` | `str \| None` | Bounding box |
| `geojson` | `dict \| None` | Geometry as GeoJSON (computed) |
| `centroid` | `tuple[float, float] \| None` | Center point `(x, y)` (computed) |
| `datasource` | `str \| None` | Data source identifier |

## Serialization

`Plot` is a Pydantic `BaseModel`, so you can serialize it:

```python
plot.model_dump()       # dict
plot.model_dump_json()  # JSON string
```

---
