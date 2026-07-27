# Estonia 🇪🇪

Parcels in Estonia come from the **Maa-amet** (Estonian Land Board). `plot-finder`
uses the INSPIRE Cadastral Parcels **WFS** for geometry and official area, and the
**in-ADS** gazetteer for the administrative units (county / municipality) that the
WFS leaves unpopulated.

```python
from plot_finder import Plot

plot = Plot(country="EE", plot_id="78401:114:0086")
```

## Querying

=== "By id (katastritunnus)"

    The `plot_id` is the cadastral unit identifier **katastritunnus**
    (e.g. `78401:114:0086`).

    ```python
    Plot(country="EE", plot_id="78401:114:0086")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326) by default. Pass
    `srid=3301` for L-EST97 coordinates.

    ```python
    Plot(country="EE", x=24.7536, y=59.437)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="EE", address="Viru väljak 4, Tallinn")
    ```

## Attributes

Sourced from the `Estonia` class:

| Attribute | Estonian term | Example |
|-----------|---------------|---------|
| `county` | maakond | `Harju maakond` |
| `municipality` | omavalitsus | `Tallinn` |
| `settlement` | asustusüksus | `Kesklinna linnaosa` |

## Notes

- **Area** is computed in **EPSG:3301** (L-EST97) and matches the Land Board's
  official *pindala*. Geometry is returned in **EPSG:4326**.
- The WFS uses **North/East** axis order for coordinate filters; `plot-finder`
  handles the transformation internally.

## Errors

| Exception | When |
|-----------|------|
| `MaaametError` | a Maa-amet WFS request failed |
| `PlotNotFoundError` | no parcel at the point / for the katastritunnus |
| `AddressNotFoundError` | the address could not be geocoded |
