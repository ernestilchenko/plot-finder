# MPZP

Query the local spatial development plan (Miejscowy Plan Zagospodarowania Przestrzennego) for a plot from the national Geoportal integration service.

---

## Installation

MPZP requires the `geo` extra:

```bash
pip install plot-finder[geo]
```

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

mpzp = analyzer.mpzp()

print(mpzp.has_plan)         # True
print(mpzp.zone_symbol)     # "MN"
print(mpzp.zone_name)       # "Tereny zabudowy mieszkaniowej jednorodzinnej"
print(mpzp.plan_name)       # "MPZP dla obszaru ..."
print(mpzp.resolution)      # "Uchwala Nr XXIII/123/2020"
print(mpzp.resolution_date) # "2020-06-15"
print(mpzp.wms_url)         # WMS map URL
```

## How It Works

1. Computes the plot centroid in EPSG:2180 (native for Polish WMS services)
2. Sends a `GetFeatureInfo` WMS request to the national MPZP integration service
3. Follows any iframe redirects in the response
4. Parses the HTML response to extract zone and plan information
5. Builds a WMS `GetMap` URL for visualization

## MPZP Model

| Field | Type | Description |
|-------|------|-------------|
| `has_plan` | `bool` | Whether an MPZP exists for this location |
| `zone_symbol` | `str \| None` | Zone designation symbol (e.g. MN, MN/U, U) |
| `zone_name` | `str \| None` | Zone description (e.g. "Tereny zabudowy mieszkaniowej") |
| `plan_name` | `str \| None` | Full plan name |
| `resolution` | `str \| None` | Council resolution number |
| `resolution_date` | `str \| None` | Resolution date (YYYY-MM-DD) |
| `publication` | `str \| None` | Publication reference |
| `effective_date` | `str \| None` | Effective date (YYYY-MM-DD) |
| `wms_url` | `str \| None` | WMS GetMap URL for the plan area |

---
