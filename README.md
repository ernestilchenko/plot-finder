# plot-finder

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

> Python library to find land parcels in **Poland** and **France** by id, address or coordinates.

One `Plot` class. `country` is required and selects the cadastre; the
country-specific attributes come from a matching class in `plot_finder.countries`.

## Installation

```bash
pip install plot-finder
```

## Poland 🇵🇱

```python
from plot_finder import Plot

plot = Plot(country="PL", plot_id="141201_1.0001.6509")
plot = Plot(country="PL", x=639231, y=486743)                  # EPSG:2180
plot = Plot(country="PL", address="Warszawa, Marszalkowska 1")

print(plot.voivodeship, plot.commune, plot.area)
```

Attributes: `voivodeship`, `county`, `commune`, `region`, `parcel`

## France 🇫🇷

```python
from plot_finder import Plot

plot = Plot(country="FR", plot_id="33063000KE0078")
plot = Plot(country="FR", x=-0.5792, y=44.8378)                # lon/lat, EPSG:4326
plot = Plot(country="FR", address="30 Rue Sainte-Catherine, Bordeaux")

print(plot.department, plot.commune, plot.area)
```

Attributes: `department`, `insee`, `commune`, `section`, `numero`

## Documentation

Full docs: [ernestilchenko.github.io/plot-finder](https://ernestilchenko.github.io/plot-finder/)

## License

MIT
