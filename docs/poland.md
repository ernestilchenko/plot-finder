# Poland 🇵🇱

`country="PL"` queries the [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) API. Coordinates are in **EPSG:2180**.

```python
from plot_finder import Plot

Plot(country="PL", plot_id="141201_1.0001.6509")        # by TERYT id
Plot(country="PL", x=639231, y=486743)                  # by coordinates
Plot(country="PL", address="Warszawa, Marszalkowska 1") # by address
```

**Attributes** (from the `Poland` class): `voivodeship`, `county`, `commune`, `region`, `parcel`

**Errors:** `ULDKError`, `PlotNotFoundError`
