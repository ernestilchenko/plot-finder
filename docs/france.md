# France 🇫🇷

`FrancePlot` queries the [IGN apicarto cadastre](https://apicarto.ign.fr/api/doc/cadastre) API. Coordinates are **lon / lat (EPSG:4326)**.

```python
from plot_finder import FrancePlot

FrancePlot(plot_id="33063000KE0078")     # by cadastral id (IDU, 14 chars)
FrancePlot(x=-0.5792, y=44.8378)         # by coordinates (lon, lat)
FrancePlot(address="Bordeaux, France")   # by address
```

**Fields:** `plot_id` (IDU), `department`, `insee`, `commune`, `section`, `numero`

**Errors:** `IGNError`, `PlotNotFoundError`

!!! note
    Id lookup does not work for Paris, Lyon and Marseille (their IDU carries the
    arrondissement code, not the base commune INSEE) — use coordinates or an address.
