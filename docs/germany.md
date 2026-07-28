# Germany 🇩🇪

Germany's cadastre (**Liegenschaftskataster / ALKIS**) is run per federal state,
with no national API. `plot-finder` routes a lookup to the right state's INSPIRE
WFS (determined from the point), then parses the parcel. Geometry is returned in
EPSG:4326.

!!! warning "Coordinates / address only, and 10 of 16 states"
    Lookup works **by coordinates or address only** (state services differ too
    much for a uniform id lookup). Free services cover **10 states**: Nordrhein-
    Westfalen, Berlin, Brandenburg, Niedersachsen, Mecklenburg-Vorpommern,
    Sachsen, Sachsen-Anhalt, Thüringen, Bremen, Hamburg. The other six
    (Bayern, Baden-Württemberg, Hessen, Rheinland-Pfalz, Schleswig-Holstein,
    Saarland) are paid/restricted and raise `ALKISError`.

```python
from plot_finder import Plot

plot = Plot(country="DE", x=6.9583, y=50.9413)   # Köln
```

## Querying

=== "By coordinates"

    Input coordinates are **longitude, latitude** (EPSG:4326).

    ```python
    Plot(country="DE", x=6.9583, y=50.9413)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim.

    ```python
    Plot(country="DE", address="Domkloster 4, Köln")
    ```

## Attributes

Sourced from the `Germany` class:

| Attribute | Meaning | Example |
|-----------|---------|---------|
| `land` | state code | `05` (NRW) |
| `gemarkung` | cadastral district | `4958` / `Mitte` |
| `flur` | field/section | `030` |
| `parcel_number` | Zähler/Nenner | `344/17` |

The `plot_id` is the state's Flurstückskennzeichen (e.g. `054958030003440017__`).

## Notes

- **Area** is computed in **EPSG:3035** (LAEA Europe, equal-area) so it is
  accurate across both German UTM zones.
- The state is detected from the point via reverse geocoding; attribute detail
  varies by state (INSPIRE CP, ALKIS-vereinfacht, or Berlin's own schema).

## Errors

| Exception | When |
|-----------|------|
| `ALKISError` | a state WFS failed, an unsupported state, or a `plot_id` lookup |
| `PlotNotFoundError` | no parcel at the point |
| `AddressNotFoundError` | the address could not be geocoded |
