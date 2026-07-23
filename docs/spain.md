# Spain 🇪🇸

`country="ES"` queries the [Dirección General del Catastro](https://www.catastro.hacienda.gob.es/) (coordinates → reference via `RCCOOR`, geometry via the INSPIRE WFS). Coordinates are **lon / lat (EPSG:4326)**.

```python
from plot_finder import Plot

Plot(country="ES", plot_id="0749407VK4704H")            # by cadastral reference
Plot(country="ES", x=-3.6999, y=40.4211)                # by coordinates (lon, lat)
Plot(country="ES", address="Calle de Alcalá 1, Madrid") # by address
```

**Attributes** (from the `Spain` class): `province`, `municipality`

**Errors:** `CatastroError`, `PlotNotFoundError`
