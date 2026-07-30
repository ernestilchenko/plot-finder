# plot-finder

[![PyPI](https://img.shields.io/pypi/v/plot-finder?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/plot-finder/)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)

One `Plot` class per country — geometry, area and the local cadastral attributes.

## Installation

```bash
pip install plot-finder
```

## Quick start

Every country supports the same three lookup modes (where the cadastre exposes them):

```python
from plot_finder import Plot

Plot(country="PL", plot_id="141201_1.0001.6509")          # by cadastral id
Plot(country="PL", x=21.0122, y=52.2297)                  # by coordinates
Plot(country="PL", address="Warszawa, Marszalkowska 1")   # by address
```

Coordinates are `lon`/`lat` in **EPSG:4326**. Set `srid=` for another output CRS.

Every `Plot` has:

```python
plot.geojson       # geometry as GeoJSON
plot.bbox          # bounding box (minx, miny, maxx, maxy)
plot.centroid      # (x, y)
plot.area          # m²
plot.datasource    # which cadastre answered
```

## Coverage

| Country | id | coords | address | Notes |
|---|:---:|:---:|:---:|---|
| [🇵🇱 Poland](#-poland) | ✓ | ✓ | ✓ | |
| [🇫🇷 France](#-france) | ✓ | ✓ | ✓ | |
| [🇪🇸 Spain](#-spain) | ✓ | ✓ | ✓ | |
| [🇳🇱 Netherlands](#-netherlands) | ✓ | ✓ | ✓ | |
| [🇨🇭 Switzerland](#-switzerland) | ✓ | ✓ | ✓ | |
| [🇪🇪 Estonia](#-estonia) | ✓ | ✓ | ✓ | |
| [🇨🇾 Cyprus](#-cyprus) | ✓ | ✓ | ✓ | |
| [🇱🇹 Lithuania](#-lithuania) | ✓ | ✓ | ✓ | |
| [🇱🇻 Latvia](#-latvia) | ✓ | ✓ | ✓ | |
| [🇵🇹 Portugal](#-portugal) | ✓ | ✓ | — | partial coverage |
| [🇸🇮 Slovenia](#-slovenia) | ✓ | ✓ | — | |
| [🇮🇹 Italy](#-italy) | — | ✓ | ✓ | excl. Trento & Bolzano |
| [🇩🇪 Germany](#-germany) | — | ✓ | ✓ | 10 of 16 states |
| [🇳🇴 Norway](#-norway) | ✓ | ✓ | ✓ | |
| [🇩🇰 Denmark](#-denmark) | ✓ | ✓ | ✓ | |
| [🇧🇪 Belgium](#-belgium) | ✓ | ✓ | ✓ | |

<br>

<details id="-poland">
<summary><b>🇵🇱 Poland</b></summary>

Attributes: `voivodeship`, `county`, `commune`, `region`, `parcel`

```python
plot = Plot(country="PL", plot_id="141201_1.0001.6509")
plot = Plot(country="PL", x=21.0122, y=52.2297)
plot = Plot(country="PL", address="Warszawa, Marszalkowska 1")

print(plot.voivodeship, plot.commune, plot.area)
```

</details>

<details id="-france">
<summary><b>🇫🇷 France</b></summary>

Attributes: `department`, `insee`, `commune`, `section`, `numero`

```python
plot = Plot(country="FR", plot_id="33063000KE0078")
plot = Plot(country="FR", x=-0.5792, y=44.8378)
plot = Plot(country="FR", address="30 Rue Sainte-Catherine, Bordeaux")

print(plot.department, plot.commune, plot.area)
```

</details>

<details id="-spain">
<summary><b>🇪🇸 Spain</b></summary>

Attributes: `province`, `municipality`

```python
plot = Plot(country="ES", plot_id="0749407VK4704H")       # cadastral reference
plot = Plot(country="ES", x=-3.6999, y=40.4211)
plot = Plot(country="ES", address="Calle de Alcalá 1, Madrid")

print(plot.province, plot.municipality, plot.area)
```

</details>

<details id="-netherlands">
<summary><b>🇳🇱 Netherlands</b></summary>

Attributes: `municipality`, `section`, `parcel_number`

```python
plot = Plot(country="NL", plot_id="AKM01 K 3785")     # cadastral designation
plot = Plot(country="NL", x=4.6255, y=52.1987)
plot = Plot(country="NL", address="Dam 1, Amsterdam")

print(plot.municipality, plot.section, plot.area)
```

</details>

<details id="-switzerland">
<summary><b>🇨🇭 Switzerland</b></summary>

Attributes: `canton`, `municipality`, `egrid`, `parcel_number`

```python
plot = Plot(country="CH", plot_id="CH119192997709")   # EGRID
plot = Plot(country="CH", x=8.5417, y=47.3769)
plot = Plot(country="CH", address="Bundesplatz 3, Bern")

print(plot.canton, plot.municipality, plot.area)
```

</details>

<details id="-estonia">
<summary><b>🇪🇪 Estonia</b></summary>

Attributes: `county`, `municipality`, `settlement`

```python
plot = Plot(country="EE", plot_id="78401:114:0086")   # katastritunnus
plot = Plot(country="EE", x=24.7536, y=59.437)
plot = Plot(country="EE", address="Viru väljak 4, Tallinn")

print(plot.county, plot.municipality, plot.area)
```

</details>

<details id="-cyprus">
<summary><b>🇨🇾 Cyprus</b></summary>

Attributes: `district_code`, `sheet`, `plan`, `parcel_number`

```python
plot = Plot(country="CY", plot_id="1000-21/450301-1-1-290")
plot = Plot(country="CY", x=33.3396, y=35.1787)
plot = Plot(country="CY", address="Nicosia, Cyprus")

print(plot.district_code, plot.parcel_number, plot.area)
```

</details>

<details id="-lithuania">
<summary><b>🇱🇹 Lithuania</b></summary>

Attributes: `cadastral_zone`, `municipality_code`, `purpose`

```python
plot = Plot(country="LT", plot_id="0101/0041:0121")   # kadastro numeris
plot = Plot(country="LT", x=25.27904, y=54.68449)
plot = Plot(country="LT", address="Gedimino pr. 1, Vilnius")

print(plot.cadastral_zone, plot.purpose, plot.area)
```

</details>

<details id="-latvia">
<summary><b>🇱🇻 Latvia</b></summary>

Attributes: `territory_code`, `group_code`, `parcel_number`

```python
plot = Plot(country="LV", plot_id="01000540120")   # kadastra apzīmējums
plot = Plot(country="LV", x=24.0917, y=56.9276)
plot = Plot(country="LV", address="Rīga, Latvia")

print(plot.territory_code, plot.parcel_number, plot.area)
```

</details>

<details id="-portugal">
<summary><b>🇵🇹 Portugal</b></summary>

Attributes: `municipality`, `parish`, `district_code`

> Partial coverage — no big cities or northern regions. Address lookup not supported.

```python
plot = Plot(country="PT", plot_id="AAA000825807")   # NIC
plot = Plot(country="PT", x=-7.7079, y=40.4210)

print(plot.municipality, plot.parish, plot.area)
```

</details>

<details id="-slovenia">
<summary><b>🇸🇮 Slovenia</b></summary>

Attributes: `ko_code`, `ko_name`, `municipality`, `parcel_number`

> Address lookup not supported.

```python
plot = Plot(country="SI", plot_id="1725-3283/1")   # KO code + parcel number
plot = Plot(country="SI", x=14.50582, y=46.05144)

print(plot.ko_name, plot.municipality, plot.area)
```

</details>

<details id="-italy">
<summary><b>🇮🇹 Italy</b></summary>

Attributes: `comune_code`, `foglio`, `particella`

> Coordinates and address only — no id lookup. Excludes Trento & Bolzano.

```python
plot = Plot(country="IT", x=12.4922, y=41.8902)
plot = Plot(country="IT", address="Piazzale degli Uffizi, Firenze")

print(plot.comune_code, plot.foglio, plot.particella, plot.area)
```

</details>

<details id="-germany">
<summary><b>🇩🇪 Germany</b></summary>

Attributes: `land`, `gemarkung`, `flur`, `parcel_number`

> Coordinates and address only — no id lookup. 10 of 16 states (free ALKIS).

```python
plot = Plot(country="DE", x=6.9583, y=50.9413)
plot = Plot(country="DE", address="Domkloster 4, Köln")

print(plot.land, plot.gemarkung, plot.parcel_number, plot.area)
```

</details>

<details id="-norway">
<summary><b>🇳🇴 Norway</b></summary>

Attributes: `municipality`, `municipality_code`, `gnr`, `bnr`

```python
plot = Plot(country="NO", plot_id="0301-209/494")   # kommunenr-gnr/bnr
plot = Plot(country="NO", x=10.7330, y=59.9116)
plot = Plot(country="NO", address="Karl Johans gate 1, Oslo")

print(plot.municipality, plot.gnr, plot.bnr, plot.area)
```

</details>

<details id="-denmark">
<summary><b>🇩🇰 Denmark</b></summary>

Attributes: `municipality`, `ejerlav`, `matrikelnr`

```python
plot = Plot(country="DK", plot_id="2000179-7000q")   # ejerlavkode-matrikelnr
plot = Plot(country="DK", x=12.5683, y=55.6761)
plot = Plot(country="DK", address="Rådhuspladsen 1, København")

print(plot.municipality, plot.ejerlav, plot.matrikelnr, plot.area)
```

</details>

<details id="-belgium">
<summary><b>🇧🇪 Belgium</b></summary>

Attributes: `nis_code`, `section`, `parcel_number`

```python
plot = Plot(country="BE", plot_id="41009A0063/00D000")   # capakey
plot = Plot(country="BE", x=4.40262, y=51.21945)
plot = Plot(country="BE", address="Grote Markt 1, Antwerpen")

print(plot.nis_code, plot.section, plot.parcel_number, plot.area)
```

</details>

<br>

## Documentation

Full docs: [ernestilchenko.github.io/plot-finder](https://ernestilchenko.github.io/plot-finder/)

## License

MIT
