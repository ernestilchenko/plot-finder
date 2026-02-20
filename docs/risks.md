# Risks

Check environmental and geological risks for a plot location — flood zones, seismic activity, soil contamination, landslides, noise pollution, and mining areas.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

report = analyzer.risks()

print(report.total_risks)  # 0

for risk in report.risks:
    print(f"{risk.name}: {risk.level} — {risk.description}")
```

## Risk Checks

The `risks()` method runs six independent checks:

| Check | Source | Description |
|-------|--------|-------------|
| **Flood** | Overpass (OSM) | Distance to rivers, streams, water bodies |
| **Seismic** | Static zones | Known seismic regions in Poland (Legnica-Głogów, Górny Śląsk, Dolny Śląsk) |
| **Soil** | Overpass (OSM) | Proximity to landfills, brownfields, industrial sites |
| **Landslide** | PIG-PIB SOPO API + regional fallback | Official landslide registry, Karpaty/Sudety fallback |
| **Noise** | GDDKiA WMS + OSM fallback | Traffic noise from strategic noise maps |
| **Mining** | Overpass (OSM) | Quarries, mine shafts, historic mines |

## RiskReport Model

| Field | Type | Description |
|-------|------|-------------|
| `risks` | `list[RiskInfo]` | List of detected risks (only those with `is_at_risk=True`) |
| `total_risks` | `int` | Number of detected risks |

## RiskInfo Model

| Field | Type | Description |
|-------|------|-------------|
| `risk_type` | `str` | Risk category: flood, seismic, soil, landslide, noise, mining |
| `name` | `str` | Polish risk name |
| `level` | `str` | Risk level: low, medium, high, unknown |
| `is_at_risk` | `bool` | Whether the plot is affected |
| `description` | `str` | Polish description with details |
| `color` | `str` | Indicator color (green / yellow / orange / red / gray) |

---
