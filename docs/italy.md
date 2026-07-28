# Italy 🇮🇹

Parcels in Italy come from **Agenzia delle Entrate** (Catasto) via its INSPIRE
Cadastral Parcels WFS. Geometry is returned in EPSG:4326.

!!! warning "Coordinates / address only"
    The Agenzia delle Entrate WFS does **not** allow filtering by cadastral
    reference, so Italy supports lookup **by coordinates or address only** — a
    `plot_id` lookup raises `AdEError`.

```python
from plot_finder import Plot

plot = Plot(country="IT", x=12.4922, y=41.8902)
```

## Querying

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326). The parcel
    containing the point is selected.

    ```python
    Plot(country="IT", x=12.4922, y=41.8902)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim (resolves to a parcel
    only when the point falls inside one — not on a road or square).

    ```python
    Plot(country="IT", address="Piazzale degli Uffizi, Firenze")
    ```

## Attributes

Sourced from the `Italy` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `comune_code` | comune cadastral (Belfiore) code | `H501` (Roma) |
| `foglio` | sheet | `0508` |
| `particella` | parcel number | `B` |

The `plot_id` is the full `NATIONALCADASTRALREFERENCE`, e.g. `H501A050800.B`.

## Notes

- **Area** is computed in **EPSG:25832** (ETRS89 / UTM 32N); no official area is
  published by the service.
- **Coverage:** nationwide **except** the autonomous provinces of **Trento** and
  **Bolzano**, whose cadastre is provincial.

## Errors

| Exception | When |
|-----------|------|
| `AdEError` | a WFS request failed, or a `plot_id` lookup was attempted |
| `PlotNotFoundError` | no parcel at the point |
| `AddressNotFoundError` | the address could not be geocoded |
