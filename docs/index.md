# plot-finder

> Find land parcels in **Poland** and **France** by id, address or coordinates.

One `Plot` class. **`country` is required** and selects the cadastre; the
country-specific attributes are sourced from a matching class in `plot_finder.countries`:

| Country | `country` | Attribute class | Data source |
|---------|-----------|-----------------|-------------|
| [Poland](poland.md) 🇵🇱 | `"PL"` | `Poland` | [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) |
| [France](france.md) 🇫🇷 | `"FR"` | `France` | [IGN apicarto cadastre](https://apicarto.ign.fr/api/doc/cadastre) |
| [Spain](spain.md) 🇪🇸 | `"ES"` | `Spain` | [Dirección General del Catastro](https://www.catastro.hacienda.gob.es/) |

```bash
pip install plot-finder
```

```python
from plot_finder import Plot

plot = Plot(country="PL", plot_id="141201_1.0001.6509")
plot.voivodeship   # country attribute, from the Poland class
plot.area          # shared computed property
```

Shared computed properties: `area` (m²), `centroid` `(x, y)`, `geojson`.
`Plot` is a Pydantic model — `model_dump()` returns a flat dict with the common
fields, the country attributes and the computed properties.
