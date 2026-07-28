# Switzerland 🇨🇭

Parcels in Switzerland come from **swisstopo** via the federal geoportal
[geo.admin.ch](https://api3.geo.admin.ch/). `plot-finder` uses the
`identify` / `find` services on the cadastral web map layer, plus the
municipality-boundary layer for the commune name.

```python
from plot_finder import Plot

plot = Plot(country="CH", plot_id="CH119192997709")
```

## Querying

=== "By id (EGRID)"

    The `plot_id` is the **EGRID** — the federal parcel identifier
    (e.g. `CH119192997709`), unique across the whole country.

    ```python
    Plot(country="CH", plot_id="CH119192997709")
    ```

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326) by default. Pass
    `in_srid=2056` to provide LV95 (CH1903+) coordinates.

    ```python
    Plot(country="CH", x=8.5417, y=47.3769)                  # (lon, lat)
    Plot(country="CH", x=2683400, y=1247500, in_srid=2056)   # LV95
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="CH", address="Bundesplatz 3, Bern")
    ```

## Attributes

Sourced from the `Switzerland` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `canton` | canton abbreviation | `ZH` |
| `municipality` | commune name | `Zürich` |
| `egrid` | federal parcel id | `CH119192997709` |
| `parcel_number` | cantonal parcel number | `AA8048` |

## Notes

- **Area** is computed in **EPSG:2056** (CH1903+ / LV95), the Swiss metric
  reference system. Geometry is returned in **EPSG:4326**.
- The cadastral layer carries the canton and EGRID; the commune name is fetched
  from the `swissboundaries3d` municipality layer at the parcel centroid.
- `parcel_number` is only unique within a municipality — use the `egrid` as the
  stable identifier.

## Errors

| Exception | When |
|-----------|------|
| `GeoAdminError` | a geo.admin.ch request failed |
| `PlotNotFoundError` | no parcel at the point / for the EGRID |
| `AddressNotFoundError` | the address could not be geocoded |
