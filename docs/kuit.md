# KUIT

KUIT (Krajowa Integracja Uzbrojenia Terenu) detects underground utility infrastructure near the plot using GUGiK WMS map analysis.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(x=18.6466, y=54.3520, srid=4326)
analyzer = PlotAnalyzer(plot)

kuit = analyzer.kuit()

if kuit.has_data:
    print(f"Water:   {kuit.water}")
    print(f"Sewage:  {kuit.sewage}")
    print(f"Gas:     {kuit.gas}")
    print(f"Power:   {kuit.power}")
    print(f"Telecom: {kuit.telecom}")
    print(f"Heating: {kuit.heating}")
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `has_data` | `bool` | Whether any utility data was found |
| `water` | `bool` | Water supply network present |
| `sewage` | `bool` | Sewage/drainage network present |
| `gas` | `bool` | Gas pipeline present |
| `power` | `bool` | Electric power network present |
| `telecom` | `bool` | Telecommunication network present |
| `heating` | `bool` | District heating network present |
| `wms_url` | `str | None` | WMS map URL showing all networks |

## How It Works

The KUIT service provides map tiles of utility infrastructure but does not expose attribute data via GetFeatureInfo. Detection works by requesting a small map tile for each utility type and checking whether the tile contains any rendered content (non-empty PNG).

!!! note "Coverage"

    Not all districts (powiaty) are included in the national integration service. Coverage is growing as more counties publish their GESUT data.

---
