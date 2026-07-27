# Netherlands 🇳🇱

Parcels in the Netherlands come from the **Kadaster** via
[PDOK](https://www.pdok.nl/) (Publieke Dienstverlening Op de Kaart), the
national open-data platform. `plot-finder` uses two PDOK services:

1. **Locatieserver** — resolves a cadastral designation (or address) to a point.
2. **Kadastrale Kaart WFS** (`kadastralekaartv5:Perceel`) — returns the parcel
   polygon and attributes for the point.

```python
from plot_finder import Plot

plot = Plot(country="NL", plot_id="AKM01 K 3785")
```

## Querying

=== "By designation"

    The `plot_id` is the **kadastrale aanduiding** — cadastral municipality code,
    section and parcel number, e.g. `AKM01 K 3785` (also accepts `AKM01-K-3785`).
    It is resolved through the PDOK Locatieserver.

    ```python
    Plot(country="NL", plot_id="AKM01 K 3785")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326) by default. Internally
    they are converted to RD New (EPSG:28992) to query the WFS. Pass
    `srid=28992` to provide RD coordinates directly.

    ```python
    Plot(country="NL", x=4.6255, y=52.1987)              # (lon, lat)
    Plot(country="NL", x=102923, y=468116, srid=28992)   # RD New
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="NL", address="Dam 1, Amsterdam")
    ```

## Attributes

Sourced from the `Netherlands` class:

| Attribute | Dutch term | Example |
|-----------|------------|---------|
| `municipality` | kadastrale gemeente | `Alkemade` |
| `section` | sectie | `K` |
| `parcel_number` | perceelnummer | `3785` |

Plus the shared fields: `plot_id` (kadastrale aanduiding), `geom_wkt`,
`datasource`, and the computed `area` / `centroid` / `geojson`.

## Notes

- **Area** is computed in **EPSG:28992** (Amersfoort / RD New), the Dutch metric
  reference system, and matches the Kadaster's *kadastrale grootte*.
- Coordinate queries select the parcel whose polygon **contains** the point,
  which is robust near shared boundaries.
- Geometry is returned in RD New and reprojected to lon/lat WKT.

## Errors

| Exception | When |
|-----------|------|
| `KadasterError` | a Locatieserver / WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the designation |
| `AddressNotFoundError` | the address could not be geocoded |
