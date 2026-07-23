# plot-finder

> Find land parcels in **Poland** and **France** by id, address or coordinates.

One class per country, both sharing a common `BasePlot` base:

| Country | Class | Data source |
|---------|-------|-------------|
| [Poland](poland.md) 🇵🇱 | `PolandPlot` | [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) |
| [France](france.md) 🇫🇷 | `FrancePlot` | [IGN apicarto cadastre](https://apicarto.ign.fr/api/doc/cadastre) |

```bash
pip install plot-finder
```

Shared computed properties: `area` (m²), `centroid` `(x, y)`, `geojson`.
Both are Pydantic models — use `model_dump()` / `model_dump_json()` to serialize.
