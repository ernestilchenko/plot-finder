# SUIKZP

Query the Study of Conditions and Directions of Spatial Development (Studium Uwarunkowan i Kierunkow Zagospodarowania Przestrzennego) from the national Geoportal integration service.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

studium = analyzer.suikzp()

print(studium.has_plan)         # True
print(studium.plan_name)        # "Studium Uwarunkowan i Kierunkow ..."
print(studium.resolution)       # "XLIX/531/2022"
print(studium.resolution_date)  # "2022-06-30"
print(studium.plan_type)        # "Studium"
print(studium.legend_url)       # URL to legend image
print(studium.document_url)     # URL to resolution PDF
print(studium.wms_url)          # WMS map URL

# Download map with plot boundary overlay (pip install plot-finder[viz])
png = analyzer.render_wms(studium.wms_url)
```

## How It Works

1. Computes the plot centroid in EPSG:2180
2. Sends a `GetFeatureInfo` WMS request to the national SUIKZP integration service (KISKZP)
3. Parses the GML response for plan metadata
4. Falls back to HTML-style parsing for municipalities with non-standard responses
5. Builds a WMS `GetMap` URL for visualization

## SUIKZP Model

| Field | Type | Description |
|-------|------|-------------|
| `has_plan` | `bool` | Whether a Studium exists for this location |
| `plan_name` | `str \| None` | Full plan name |
| `resolution` | `str \| None` | Council resolution number |
| `resolution_date` | `str \| None` | Adoption date (YYYY-MM-DD) |
| `plan_type` | `str \| None` | Document type (e.g. "Studium") |
| `legend_url` | `str \| None` | URL to legend image |
| `document_url` | `str \| None` | URL to resolution document (PDF) |
| `wms_url` | `str \| None` | WMS GetMap URL for the plan area |

---
