# plot-finder

Query Polish ULDK (GUGiK) API to find land parcels by TERYT ID or coordinates.

## Installation

```bash
pip install plot-finder
```

## Usage

### By TERYT ID

```python
from plot_finder import Plot

plot = Plot(plot="141201_1.0001.6509")
print(plot.voivodeship)  # mazowieckie
print(plot.commune)      # Mińsk Mazowiecki (miasto)
print(plot.parcel)       # 6509
print(plot.geom_wkt)     # POLYGON((...))
print(plot.geojson)      # {"type": "Polygon", "coordinates": [...]}
```

### By coordinates

```python
# Default EPSG:2180
plot = Plot(x=460166.4, y=313380.5)

# WGS84
plot = Plot(x=21.5896, y=52.1717, srid=4326)
```

### Choose SRID for output geometry

```python
plot = Plot(plot="141201_1.0001.6509", srid=4326)
print(plot.geojson)  # coordinates in WGS84
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `plot` | `str` | TERYT ID |
| `x`, `y` | `float` | Search coordinates |
| `srid` | `int` | Coordinate system (default: 2180) |
| `voivodeship` | `str` | Województwo |
| `county` | `str` | Powiat |
| `commune` | `str` | Gmina |
| `region` | `str` | Obręb |
| `parcel` | `str` | Numer działki |
| `geom_wkt` | `str` | Geometry as WKT |
| `geom_extent` | `str` | Bounding box |
| `geojson` | `dict` | Geometry as GeoJSON |
| `datasource` | `str` | Data source |

## License

MIT
