# Belgium 🇧🇪

Parcels in Belgium come from **FPS Finance** (AAPD/CadGIS) via its free, no-auth
federal INSPIRE Cadastral Parcels service — national coverage (Flanders,
Wallonia, Brussels). Geometry is returned in EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="BE", plot_id="41009A0063/00D000")
```

## Querying

=== "By id (capakey)"

    The `plot_id` is the **capakey** (`nationalCadastralRef`),
    e.g. `41009A0063/00D000`.

    ```python
    Plot(country="BE", plot_id="41009A0063/00D000")
    ```

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326).

    ```python
    Plot(country="BE", x=4.40262, y=51.21945)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="BE", address="Grote Markt 1, Antwerpen")
    ```

## Attributes

Sourced from the `Belgium` class (parsed from the capakey):

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `nis_code` | municipality NIS code | `11803` |
| `section` | cadastral section | `C` |
| `parcel_number` | parcel label | `2165M` |

The `plot_id` is the full capakey. The dataset carries the municipality NIS code
(not its name).

## Notes

- **Area** is the geodesic area on the WGS84 ellipsoid; it matches the official
  `areaValue` within rounding.
- Points on public domain (streets, rivers, rail) belong to no parcel and raise
  `PlotNotFoundError`.

## Errors

| Exception | When |
|-----------|------|
| `CadGISError` | a CadGIS request failed |
| `PlotNotFoundError` | no parcel at the point / for the capakey |
| `AddressNotFoundError` | the address could not be geocoded |
