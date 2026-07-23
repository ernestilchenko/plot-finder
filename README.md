# plot-finder

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

> Python library to find land parcels in **Poland** and **France** by id, address or coordinates.

## Installation

```bash
pip install plot-finder
```

## Poland 🇵🇱

```python
from plot_finder import PolandPlot

plot = PolandPlot(plot_id="141201_1.0001.6509")
plot = PolandPlot(x=639231, y=486743)
plot = PolandPlot(address="Warszawa, Marszalkowska 1")

print(plot.voivodeship, plot.commune, plot.area)
```

## France 🇫🇷

```python
from plot_finder import FrancePlot

plot = FrancePlot(plot_id="33063000KE0078")
plot = FrancePlot(x=-0.5792, y=44.8378)
plot = FrancePlot(address="Bordeaux, France")

print(plot.department, plot.commune, plot.area)
```

## Documentation

Full docs: [ernestilchenko.github.io/plot-finder](https://ernestilchenko.github.io/plot-finder/)

## License

MIT
