# Poland 🇵🇱

`PolandPlot` queries the [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) API. Coordinates are in **EPSG:2180**.

```python
from plot_finder import PolandPlot

PolandPlot(plot_id="141201_1.0001.6509")        # by TERYT id
PolandPlot(x=639231, y=486743)                  # by coordinates
PolandPlot(address="Warszawa, Marszalkowska 1") # by address
```

**Fields:** `plot_id` (TERYT), `voivodeship`, `county`, `commune`, `region`, `parcel`

**Errors:** `ULDKError`, `PlotNotFoundError`
