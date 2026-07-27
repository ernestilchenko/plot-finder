# France 🇫🇷

Parcels in France come from the **IGN apicarto cadastre** API
([documentation](https://apicarto.ign.fr/api/doc/cadastre)), served by the
Institut national de l'information géographique et forestière. Geometry is
returned as GeoJSON in **longitude / latitude (EPSG:4326)**.

```python
from plot_finder import Plot

plot = Plot(country="FR", plot_id="33063000KE0078")
```

## Querying

=== "By id (IDU)"

    The identifier is the 14-character cadastral **IDU**, laid out as
    `code_insee(5) + com_abs(3) + section(2) + numero(4)`.

    ```python
    Plot(country="FR", plot_id="33063000KE0078")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326). The API returns the
    parcel whose geometry contains the point.

    ```python
    Plot(country="FR", x=-0.5792, y=44.8378)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="FR", address="30 Rue Sainte-Catherine, Bordeaux")
    ```

## Attributes

Sourced from the `France` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `department` | department code (`code_dep`) | `33` |
| `insee` | commune INSEE code | `33063` |
| `commune` | commune name | `Bordeaux` |
| `section` | cadastral section | `KE` |
| `numero` | parcel number | `0078` |

Plus the shared fields: `plot_id` (IDU), `geom_wkt`, `datasource`, and the
computed `area` / `centroid` / `geojson`.

## Notes

- **Area** is computed in **EPSG:2154** (RGF93 / Lambert-93), the French metric
  reference system.
- Coordinates are always **lon, lat** — a common mistake is to swap them.

!!! warning "Paris, Lyon and Marseille"
    For these three cities the IDU carries the **arrondissement** code instead
    of the base commune INSEE, so **id lookup does not work**. Use coordinates
    or an address for parcels in Paris, Lyon or Marseille.

## Errors

| Exception | When |
|-----------|------|
| `IGNError` | the apicarto request failed or returned invalid data |
| `PlotNotFoundError` | no parcel matched the id / coordinates |
| `AddressNotFoundError` | the address could not be geocoded |
