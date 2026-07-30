# Denmark 🇩🇰

Parcels in Denmark come from **SDFI** (the cadastre, *Matriklen*) via the free,
open **DAWA** API (`api.dataforsyningen.dk`) — no key or token. Geometry is
returned in EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="DK", plot_id="2000179-7000q")
```

## Querying

=== "By id (matrikel)"

    The `plot_id` is `ejerlavkode-matrikelnr` (cadastral district code + parcel
    number), e.g. `2000179-7000q`.

    ```python
    Plot(country="DK", plot_id="2000179-7000q")
    ```

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326).

    ```python
    Plot(country="DK", x=12.5683, y=55.6761)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="DK", address="Rådhuspladsen 1, København")
    ```

## Attributes

Sourced from the `Denmark` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `municipality` | kommune | `København` |
| `ejerlav` | cadastral district (ejerlav) | `Vestervold Kvarter, København` |
| `matrikelnr` | parcel number | `7000q` |

## Notes

- **Area** is the geodesic area on the WGS84 ellipsoid; it matches DAWA's
  official *registreretareal* within rounding.
- A point outside any parcel (e.g. at sea) raises `PlotNotFoundError`.

## Errors

| Exception | When |
|-----------|------|
| `DAWAError` | a DAWA request failed |
| `PlotNotFoundError` | no parcel at the point / for the matrikel |
| `AddressNotFoundError` | the address could not be geocoded |
