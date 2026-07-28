# Slovenia 🇸🇮

Parcels in Slovenia come from **GURS** (Geodetska uprava RS) via the e-prostor
Kataster nepremičnin (KN) WFS. Geometry is returned in EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="SI", plot_id="1725-3283/1")
```

## Querying

=== "By id (KO + parcel)"

    The `plot_id` is the cadastral municipality code (katastrska občina) plus the
    parcel number, e.g. `1725-3283/1` (also accepts `1725 3283/1`).

    ```python
    Plot(country="SI", plot_id="1725-3283/1")
    ```

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326). Pass `in_srid=3794`
    for D96/TM coordinates.

    ```python
    Plot(country="SI", x=14.50582, y=46.05144)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="SI", address="Prešernov trg 1, Ljubljana")
    ```

## Attributes

Sourced from the `Slovenia` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `ko_code` | katastrska občina code | `1725` |
| `ko_name` | KO code + name | `1725 AJDOVŠČINA` |
| `municipality` | občina | `Ljubljana` |
| `parcel_number` | parcelna številka | `3283/1` |

## Notes

- **Area** is computed in **EPSG:3794** (D96/TM) and matches the GURS official
  *površina*.
- The municipality (`občina`) is fetched from a second GURS layer — best effort.

## Errors

| Exception | When |
|-----------|------|
| `GURSError` | a GURS WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the id |
| `AddressNotFoundError` | the address could not be geocoded |
