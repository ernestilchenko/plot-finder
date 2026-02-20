# GUGiK Integration

Fetch spatial data services registered in the GUGiK integration portal (eziudp) for a given plot's TERYT identifier.

---

## Installation

GUGiK queries require the `geo` extra:

```bash
pip install plot-finder[geo]
```

## Usage

```python
from plot_finder import Plot

plot = Plot(plot_id="141201_1.0001.6509")

for entry in plot.gugik():
    print(f"{entry.organ}: {entry.nazwa}")
    if entry.wms:
        print(f"  WMS: {entry.wms}")
    if entry.wfs:
        print(f"  WFS: {entry.wfs}")
```

## How It Works

Queries `integracja.gugik.gov.pl/eziudp` with the plot's TERYT identifier and parses the HTML table of registered spatial data services. Returns a list of entries with the responsible authority, dataset name, and WMS/WFS service URLs.

## GugikEntry Model

| Field | Type | Description |
|-------|------|-------------|
| `organ` | `str` | Responsible authority name |
| `nazwa` | `str` | Dataset / service name |
| `wms` | `str \| None` | WMS service URL (if available) |
| `wfs` | `str \| None` | WFS service URL (if available) |

---
