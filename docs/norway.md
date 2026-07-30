# Norway 🇳🇴

Parcels in Norway come from **Kartverket** (the Norwegian Mapping Authority) via
the Matrikkelen "Eiendomskart Teig" WFS on Geonorge. Geometry is returned in
EPSG:4326.

```python
from plot_finder import Plot

plot = Plot(country="NO", plot_id="0301-209/494")
```

## Querying

=== "By id (matrikkelnummer)"

    The `plot_id` is `kommunenr-gnr/bnr` (municipality, gårdsnummer, bruksnummer),
    e.g. `0301-209/494`.

    ```python
    Plot(country="NO", plot_id="0301-209/494")
    ```

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326).

    ```python
    Plot(country="NO", x=10.7330, y=59.9116)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="NO", address="Karl Johans gate 1, Oslo")
    ```

## Attributes

Sourced from the `Norway` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `municipality` | kommune name | `OSLO` |
| `municipality_code` | kommunenummer | `0301` |
| `gnr` | gårdsnummer | `209` |
| `bnr` | bruksnummer | `494` |

## Notes

- **Area** is the geodesic area on the WGS84 ellipsoid; it matches the official
  Matrikkelen *lagretBeregnetAreal* within rounding.
- The Kartverket WFS is GML-only and needs an XML POST filter — handled
  internally.

## Errors

| Exception | When |
|-----------|------|
| `KartverketError` | a Kartverket WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the matrikkelnummer |
| `AddressNotFoundError` | the address could not be geocoded |
