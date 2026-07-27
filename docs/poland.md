# Poland 🇵🇱

Parcels in Poland come from the **ULDK** service of [GUGiK](https://uldk.gugik.gov.pl/)
(Główny Urząd Geodezji i Kartografii), the national mapping authority. The
service returns the parcel geometry together with the full administrative
breakdown (voivodeship → county → commune → cadastral region → parcel).

```python
from plot_finder import Plot

plot = Plot(country="PL", plot_id="141201_1.0001.6509")
```

## Querying

=== "By id (TERYT)"

    The parcel identifier is the **TERYT** number.

    ```python
    Plot(country="PL", plot_id="141201_1.0001.6509")
    ```

=== "By coordinates"

    Coordinates default to **EPSG:2180** (the Polish national grid). Pass
    `srid=` to use another CRS.

    ```python
    Plot(country="PL", x=639231, y=486743)             # EPSG:2180
    Plot(country="PL", x=21.0, y=52.2, srid=4326)      # lon/lat
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim, then resolved to a
    parcel.

    ```python
    Plot(country="PL", address="Warszawa, Marszalkowska 1")
    ```

## Attributes

Sourced from the `Poland` class and exposed flat on the plot:

| Attribute | Polish term | Example |
|-----------|-------------|---------|
| `voivodeship` | województwo | `mazowieckie` |
| `county` | powiat | `powiat m. Warszawa` |
| `commune` | gmina | `Warszawa (miasto)` |
| `region` | obręb ewidencyjny | `Śródmieście` |
| `parcel` | numer działki | `6509` |

Plus the shared fields: `plot_id` (TERYT), `geom_wkt`, `geom_extent`,
`datasource`, and the computed `area` / `centroid` / `geojson`.

## Notes

- **Area** is computed in **EPSG:2180**. If the parcel was fetched in another
  CRS (e.g. `srid=4326`), the geometry is reprojected before measuring.
- The ULDK service accepts geographic coordinates too — passing `srid=4326`
  simply forwards it to the API.

## Errors

| Exception | When |
|-----------|------|
| `ULDKError` | the ULDK request failed or returned an unexpected response |
| `PlotNotFoundError` | no parcel matched the id / coordinates |
| `AddressNotFoundError` | the address could not be geocoded |
