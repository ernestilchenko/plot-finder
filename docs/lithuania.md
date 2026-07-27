# Lithuania 🇱🇹

Parcels in Lithuania come from **Registrų centras** via the national INSPIRE
geoportal ([geoportal.lt](https://www.inspire-geoportal.lt/)). Geometry is
returned in EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="LT", plot_id="0101/0041:0121")
```

## Querying

=== "By id (kadastro numeris)"

    The `plot_id` is the cadastral number **kadastro numeris**
    (e.g. `0101/0041:0121`).

    ```python
    Plot(country="LT", plot_id="0101/0041:0121")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326). Pass `in_srid=3346` for
    LKS-94 coordinates.

    ```python
    Plot(country="LT", x=25.27904, y=54.68449)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="LT", address="Gedimino pr. 1, Vilnius")
    ```

## Attributes

Sourced from the `Lithuania` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `cadastral_zone` | cadastral zone (label prefix) | `0101` |
| `municipality_code` | savivaldybė code | `13` |
| `purpose` | land use purpose | `Other, 995` |

## Notes

- **Area** is computed in **EPSG:3346** (LKS-94) and matches the official
  *plotas*.
- The WFS uses **lat/lon** axis order for coordinate filters; `plot-finder`
  handles it internally.

## Errors

| Exception | When |
|-----------|------|
| `RCError` | a geoportal.lt WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the kadastro numeris |
| `AddressNotFoundError` | the address could not be geocoded |
