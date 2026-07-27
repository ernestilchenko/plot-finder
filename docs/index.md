# plot-finder

> Find land parcels across Europe by **id**, **address** or **coordinates** — one API, one object.

`plot-finder` wraps the official open cadastre of each supported country behind a
single [`Plot`](reference.md) class. You pick the country, pass a query, and get
back a normalized parcel with geometry, area, centroid and country-specific
attributes.

```python
from plot_finder import Plot

plot = Plot(country="PL", plot_id="141201_1.0001.6509")
plot.voivodeship   # 'mazowieckie'  — country attribute (from the Poland class)
plot.area          # 6509.0         — shared, computed from geometry
plot.centroid      # (x, y)
```

## Supported countries

| Country | `country` | Attribute class | Data source | Coordinates |
|---------|-----------|-----------------|-------------|-------------|
| [Poland](poland.md) 🇵🇱 | `"PL"` | `Poland` | [ULDK / GUGiK](https://uldk.gugik.gov.pl/) | EPSG:2180 |
| [France](france.md) 🇫🇷 | `"FR"` | `France` | [IGN apicarto cadastre](https://apicarto.ign.fr/api/doc/cadastre) | lon/lat (EPSG:4326) |
| [Spain](spain.md) 🇪🇸 | `"ES"` | `Spain` | [Dirección General del Catastro](https://www.catastro.hacienda.gob.es/) | lon/lat (EPSG:4326) |
| [Netherlands](netherlands.md) 🇳🇱 | `"NL"` | `Netherlands` | [PDOK Kadaster](https://www.pdok.nl/) | lon/lat (EPSG:4326) |
| [Switzerland](switzerland.md) 🇨🇭 | `"CH"` | `Switzerland` | [swisstopo / geo.admin.ch](https://api3.geo.admin.ch/) | lon/lat (EPSG:4326) |
| [Estonia](estonia.md) 🇪🇪 | `"EE"` | `Estonia` | [Maa-amet](https://geoportaal.maaamet.ee/) | lon/lat (EPSG:4326) |
| [Cyprus](cyprus.md) 🇨🇾 | `"CY"` | `Cyprus` | [DLS (Lands & Surveys)](https://portal.dls.moi.gov.cy/) | lon/lat (EPSG:4326) |
| [Lithuania](lithuania.md) 🇱🇹 | `"LT"` | `Lithuania` | [Registrų centras (geoportal.lt)](https://www.inspire-geoportal.lt/) | lon/lat (EPSG:4326) |
| [Latvia](latvia.md) 🇱🇻 | `"LV"` | `Latvia` | [VZD (kadastrs.lv)](https://www.kadastrs.lv/) | lon/lat (EPSG:4326) |
| [Portugal](portugal.md) 🇵🇹 | `"PT"` | `Portugal` | [DGT SNIC](https://snic.dgterritorio.gov.pt/) | lon/lat (EPSG:4326) |

## Installation

```bash
pip install plot-finder
```

**Requirements:** Python 3.10+ · `pydantic` `httpx` `shapely` `pyproj`

## How it works

`country` is **required** and selects which cadastre to query. Every country has
a matching class in `plot_finder.countries` (`Poland`, `France`, `Spain`,
`Netherlands`) that:

1. defines the country-specific **attributes** (e.g. `voivodeship`, `department`),
2. knows how to **fetch** a parcel from that country's API,
3. declares the **metric CRS** used to compute the area.

The `Plot` sources those attributes from the matching class and exposes them
**flat**, next to the shared fields:

```python
Plot(country="FR", x=-0.5792, y=44.8378).department   # from the France class
Plot(country="ES", x=-3.6999, y=40.4211).province      # from the Spain class
```

## Three ways to query

Every country supports the same three entry points (details and formats differ
per country — see each page):

```python
Plot(country="PL", plot_id="...")                 # by cadastral id / reference
Plot(country="PL", x=639231, y=486743)            # by coordinates
Plot(country="PL", address="Warszawa, ...")       # by address (geocoded)
```

Addresses are geocoded with [OpenStreetMap Nominatim](https://nominatim.org/);
you must provide at least one of `plot_id`, `address`, or both `x` and `y`.

## Shared properties

Regardless of country, every `Plot` exposes:

| Property   | Type | Description |
|------------|------|-------------|
| `area`     | `float` | Parcel area in **m²**, computed from the geometry in the country's metric CRS |
| `centroid` | `(float, float)` | Centroid of the geometry |
| `geojson`  | `dict` | Geometry as a GeoJSON mapping |
| `geom_wkt` | `str` | Geometry as WKT |

## Coordinate systems

Geometry is always returned in **EPSG:4326** (lon/lat) by default. To get it in
another CRS, set `srid`:

```python
Plot(country="PL", x=639231, y=486743)             # geometry in EPSG:4326
Plot(country="PL", x=639231, y=486743, srid=2180)  # geometry in EPSG:2180
```

Input coordinates are read in each country's native CRS (e.g. EPSG:2180 for
Poland, EPSG:4326 for the rest). Override with `in_srid`:

```python
Plot(country="CH", x=2683400, y=1247500, in_srid=2056)   # LV95 input, 4326 output
```

## Serialization

`Plot` is a Pydantic v2 model, so a parcel round-trips to plain data:

```python
plot.model_dump()        # flat dict: common fields + country attributes + computed props
plot.model_dump_json()   # JSON string
```

## Errors

```python
from plot_finder import (
    PlotNotFoundError,     # no parcel for the given query
    AddressNotFoundError,  # geocoder returned no result
    ULDKError,             # Poland (ULDK) API failure
    IGNError,              # France (IGN) API failure
    CatastroError,         # Spain (Catastro) API failure
    KadasterError,         # Netherlands (PDOK Kadaster) API failure
    GeoAdminError,         # Switzerland (geo.admin.ch) API failure
    MaaametError,          # Estonia (Maa-amet) API failure
    DLSError,              # Cyprus (DLS) API failure
    RCError,               # Lithuania (geoportal.lt) API failure
    VZDError,              # Latvia (VZD) API failure
    DGTError,              # Portugal (DGT SNIC) API failure
)
```

See the [reference](reference.md) for the full field list and model details.
