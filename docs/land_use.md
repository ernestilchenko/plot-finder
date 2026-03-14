# Land Use

Official land use classification from Krajowa Integracja Użytków Gruntowych (GUGiK).

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=17.9213, y=50.6751, srid=4326)
analyzer = PlotAnalyzer(plot)

lu = analyzer.land_use()

if lu.has_data:
    print(f"Plot ID: {lu.plot_id}")
    print(f"Area: {lu.area_ha} ha")
    print(f"Use code: {lu.use_code}")
    print(f"Use name: {lu.use_name}")

    # Download map with plot boundary overlay (pip install plot-finder[viz])
    png = analyzer.render_wms(lu.wms_url)
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `has_data` | `bool` | Whether land use data was found |
| `plot_id` | `str | None` | Cadastral parcel ID |
| `area_ha` | `float | None` | Parcel area in hectares |
| `use_code` | `str | None` | Land use codes (e.g. `B,Bi`, `RIVb`, `Ls`) |
| `use_name` | `str | None` | Human-readable name (e.g. "Tereny mieszkaniowe") |
| `registry_group` | `str | None` | Registry group number |
| `wms_url` | `str | None` | WMS map URL |

## Land Use Codes

| Code | Description |
|------|-------------|
| `R` | Grunty orne (arable land) |
| `S` | Sady (orchards) |
| `Ł` | Łąki trwałe (permanent meadows) |
| `Ps` | Pastwiska trwałe (permanent pastures) |
| `Ls` | Lasy (forests) |
| `Lz` | Grunty zadrzewione i zakrzewione (wooded land) |
| `B` | Tereny mieszkaniowe (residential) |
| `Ba` | Tereny przemysłowe (industrial) |
| `Bi` | Inne tereny zabudowane (other built-up) |
| `Bp` | Zurbanizowane tereny niezabudowane (undeveloped urban) |
| `Bz` | Tereny rekreacyjno-wypoczynkowe (recreational) |
| `K` | Użytki kopalne (mining land) |
| `dr` | Drogi (roads) |
| `N` | Nieużytki (wasteland) |
| `W` | Grunty pod wodami (water land) |

Codes may include quality class suffixes (e.g. `RIVb` = arable land, class IVb).

---
