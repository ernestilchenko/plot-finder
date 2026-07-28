# plot-finder

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

> Python library to find land parcels across Europe — **Poland**, **France**, **Spain**, **Netherlands**, **Switzerland**, **Estonia**, **Cyprus**, **Lithuania**, **Latvia**, **Portugal**, **Slovenia**, **Italy** and **Germany** — by id, address or coordinates.
>
> Geometry is returned in **EPSG:4326** by default (set `srid=` for another CRS).

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

## Spain 🇪🇸

```python
from plot_finder import Plot

plot = Plot(country="ES", plot_id="0749407VK4704H")       # cadastral reference
plot = Plot(country="ES", x=-3.6999, y=40.4211)           # lon/lat, EPSG:4326
plot = Plot(country="ES", address="Calle de Alcalá 1, Madrid")

print(plot.province, plot.municipality, plot.area)
```

Attributes: `province`, `municipality`

## Netherlands 🇳🇱

```python
from plot_finder import Plot

plot = Plot(country="NL", plot_id="AKM01 K 3785")     # cadastral designation
plot = Plot(country="NL", x=4.6255, y=52.1987)        # lon/lat, EPSG:4326
plot = Plot(country="NL", address="Dam 1, Amsterdam")

print(plot.municipality, plot.section, plot.area)
```

Attributes: `municipality`, `section`, `parcel_number`

## Switzerland 🇨🇭

```python
from plot_finder import Plot

plot = Plot(country="CH", plot_id="CH119192997709")   # EGRID
plot = Plot(country="CH", x=8.5417, y=47.3769)        # lon/lat, EPSG:4326
plot = Plot(country="CH", address="Bundesplatz 3, Bern")

print(plot.canton, plot.municipality, plot.area)
```

Attributes: `canton`, `municipality`, `egrid`, `parcel_number`

## Estonia 🇪🇪

```python
from plot_finder import Plot

plot = Plot(country="EE", plot_id="78401:114:0086")   # katastritunnus
plot = Plot(country="EE", x=24.7536, y=59.437)        # lon/lat, EPSG:4326
plot = Plot(country="EE", address="Viru väljak 4, Tallinn")

print(plot.county, plot.municipality, plot.area)
```

Attributes: `county`, `municipality`, `settlement`

## Cyprus 🇨🇾

```python
from plot_finder import Plot

plot = Plot(country="CY", plot_id="1000-21/450301-1-1-290")   # cadastral reference
plot = Plot(country="CY", x=33.3396, y=35.1787)               # lon/lat, EPSG:4326
plot = Plot(country="CY", address="Nicosia, Cyprus")

print(plot.district_code, plot.parcel_number, plot.area)
```

Attributes: `district_code`, `sheet`, `plan`, `parcel_number`

## Lithuania 🇱🇹

```python
from plot_finder import Plot

plot = Plot(country="LT", plot_id="0101/0041:0121")   # kadastro numeris
plot = Plot(country="LT", x=25.27904, y=54.68449)     # lon/lat, EPSG:4326
plot = Plot(country="LT", address="Gedimino pr. 1, Vilnius")

print(plot.cadastral_zone, plot.purpose, plot.area)
```

Attributes: `cadastral_zone`, `municipality_code`, `purpose`

## Latvia 🇱🇻

```python
from plot_finder import Plot

plot = Plot(country="LV", plot_id="01000540120")   # kadastra apzīmējums
plot = Plot(country="LV", x=24.0917, y=56.9276)    # lon/lat, EPSG:4326
plot = Plot(country="LV", address="Rīga, Latvia")

print(plot.territory_code, plot.parcel_number, plot.area)
```

Attributes: `territory_code`, `group_code`, `parcel_number`

## Portugal 🇵🇹

```python
from plot_finder import Plot

plot = Plot(country="PT", plot_id="AAA000825807")   # NIC
plot = Plot(country="PT", x=-7.7079, y=40.4210)     # lon/lat, EPSG:4326

print(plot.municipality, plot.parish, plot.area)
```

Attributes: `municipality`, `parish`, `district_code` — _partial coverage (no big cities/north)._

## Slovenia 🇸🇮

```python
from plot_finder import Plot

plot = Plot(country="SI", plot_id="1725-3283/1")   # KO code + parcel number
plot = Plot(country="SI", x=14.50582, y=46.05144)  # lon/lat, EPSG:4326

print(plot.ko_name, plot.municipality, plot.area)
```

Attributes: `ko_code`, `ko_name`, `municipality`, `parcel_number`

## Italy 🇮🇹

```python
from plot_finder import Plot

plot = Plot(country="IT", x=12.4922, y=41.8902)   # lon/lat, EPSG:4326
plot = Plot(country="IT", address="Piazzale degli Uffizi, Firenze")

print(plot.comune_code, plot.foglio, plot.particella, plot.area)
```

Attributes: `comune_code`, `foglio`, `particella` — _coordinates/address only (no id lookup); excludes Trento & Bolzano._

## Germany 🇩🇪

```python
from plot_finder import Plot

plot = Plot(country="DE", x=6.9583, y=50.9413)   # lon/lat, EPSG:4326
plot = Plot(country="DE", address="Domkloster 4, Köln")

print(plot.land, plot.gemarkung, plot.parcel_number, plot.area)
```

Attributes: `land`, `gemarkung`, `flur`, `parcel_number` — _coordinates/address only; 10 of 16 states (free ALKIS)._

## Documentation

Full docs: [ernestilchenko.github.io/plot-finder](https://ernestilchenko.github.io/plot-finder/)

## License

MIT
