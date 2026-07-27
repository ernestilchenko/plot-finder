# Latvia 🇱🇻

Parcels in Latvia come from **Valsts zemes dienests** (VZD, State Land Service)
via its public INSPIRE Cadastral Parcels WFS. Geometry is returned in EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="LV", plot_id="01000540120")
```

## Querying

=== "By id (kadastra apzīmējums)"

    The `plot_id` is the 11-digit parcel designation **kadastra apzīmējums**
    (e.g. `01000540120`).

    ```python
    Plot(country="LV", plot_id="01000540120")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326). Pass `in_srid=3059` for
    LKS-92 coordinates.

    ```python
    Plot(country="LV", x=24.0917, y=56.9276)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="LV", address="Rīga, Latvia")
    ```

## Attributes

Sourced from the `Latvia` class (parsed from the designation):

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `territory_code` | cadastral territory | `0100` |
| `group_code` | cadastral group | `054` |
| `parcel_number` | parcel number | `0120` |

## Notes

- **Area** is computed in **EPSG:3059** (LKS-92 / Latvia TM) and matches the VZD
  `areaValue`.
- The WFS uses **lat/lon** axis order for coordinate filters; `plot-finder`
  handles it internally.

## Errors

| Exception | When |
|-----------|------|
| `VZDError` | a VZD WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the designation |
| `AddressNotFoundError` | the address could not be geocoded |
