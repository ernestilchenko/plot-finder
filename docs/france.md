# France 🇫🇷

`country="FR"` queries the [IGN apicarto cadastre](https://apicarto.ign.fr/api/doc/cadastre) API. Coordinates are **lon / lat (EPSG:4326)**.

```python
from plot_finder import Plot

Plot(country="FR", plot_id="33063000KE0078")                    # by cadastral id (IDU, 14 chars)
Plot(country="FR", x=-0.5792, y=44.8378)                        # by coordinates (lon, lat)
Plot(country="FR", address="30 Rue Sainte-Catherine, Bordeaux") # by address
```

**Attributes** (from the `France` class): `department`, `insee`, `commune`, `section`, `numero`

**Errors:** `IGNError`, `PlotNotFoundError`

!!! note
    Id lookup does not work for Paris, Lyon and Marseille (their IDU carries the
    arrondissement code, not the base commune INSEE) — use coordinates or an address.
