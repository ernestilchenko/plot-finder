# Portugal 🇵🇹

Parcels in Portugal come from the **DGT SNIC** (Sistema Nacional de Informação
Cadastral, Direção-Geral do Território). Geometry is returned in EPSG:4326.

!!! warning "Partial coverage"
    Portugal's cadastre is incomplete. SNIC covers mostly the rural centre and
    south of the mainland — **major cities (Lisbon, Porto, Coimbra) and the north
    return no parcel**, and a lookup there raises `PlotNotFoundError`.

```python
from plot_finder import Plot

plot = Plot(country="PT", plot_id="AAA000825807")
```

## Querying

=== "By id (NIC)"

    The `plot_id` is the **NIC** (Número de Identificação de Prédio),
    e.g. `AAA000825807`.

    ```python
    Plot(country="PT", plot_id="AAA000825807")
    ```

=== "By coordinates"

    Coordinates are **longitude, latitude** (EPSG:4326). The parcel containing the
    point is selected.

    ```python
    Plot(country="PT", x=-7.7079, y=40.4210)   # (lon, lat)
    ```

=== "By address"

    The address is geocoded with OpenStreetMap Nominatim (only resolves inside the
    cadastred area).

    ```python
    Plot(country="PT", address="Seia, Portugal")
    ```

## Attributes

Sourced from the `Portugal` class:

| Attribute | Portuguese term | Example |
|-----------|-----------------|---------|
| `municipality` | concelho | `SEIA` |
| `parish` | freguesia | `Seia, São Romão e Lapa dos Dinheiros` |
| `district_code` | código dico | `0912` |

## Notes

- **Area** is computed in **EPSG:3763** (ETRS89 / PT-TM06) and matches the SNIC
  official `area_m2`.
- Coverage is partial — always handle `PlotNotFoundError`.

## Errors

| Exception | When |
|-----------|------|
| `DGTError` | a DGT SNIC request failed |
| `PlotNotFoundError` | no parcel at the point / for the NIC (or outside coverage) |
| `AddressNotFoundError` | the address could not be geocoded |
