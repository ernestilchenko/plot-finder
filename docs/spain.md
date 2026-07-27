# Spain 🇪🇸

Parcels in Spain come from the **Dirección General del Catastro** (DGC). Because
no single endpoint returns everything, `plot-finder` combines three official
services:

1. **`Consulta_RCCOOR`** — coordinates → cadastral reference (*referencia catastral*).
2. **INSPIRE WFS** (`GetParcel`) — reference → parcel geometry + official area.
3. **`Consulta_DNPRC`** — reference → province and municipality.

```python
from plot_finder import Plot

plot = Plot(country="ES", plot_id="0749407VK4704H")
```

## Querying

=== "By reference"

    The `plot_id` is the **referencia catastral** (14 characters for the parcel).

    ```python
    Plot(country="ES", plot_id="0749407VK4704H")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326). They are resolved to a
    cadastral reference via `RCCOOR`, then to geometry.

    ```python
    Plot(country="ES", x=-3.6999, y=40.4211)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="ES", address="Calle de Alcalá 1, Madrid")
    ```

## Attributes

Sourced from the `Spain` class:

| Attribute | Spanish term | Example |
|-----------|--------------|---------|
| `province` | provincia | `MADRID` |
| `municipality` | municipio | `MADRID` |

Plus the shared fields: `plot_id` (referencia catastral), `geom_wkt`,
`datasource`, and the computed `area` / `centroid` / `geojson`.

## Notes

- **Area** is computed in **EPSG:25830** (ETRS89 / UTM zone 30N). It matches the
  Catastro's official *superficie* to within a fraction of a percent.
- The INSPIRE WFS returns geometry as GML in **lat/lon** axis order;
  `plot-finder` normalizes it to standard **lon/lat** WKT.
- The geometry request uses the 14-character parcel reference; a longer 20-char
  property reference is truncated to its parcel part.

## Errors

| Exception | When |
|-----------|------|
| `CatastroError` | an RCCOOR / WFS request failed or returned invalid data |
| `PlotNotFoundError` | no parcel at the point / for the reference |
| `AddressNotFoundError` | the address could not be geocoded |
