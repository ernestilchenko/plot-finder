# POG

Query the General Municipal Plan (Plan Ogolny Gminy) from the national Geoportal service. POG is a new spatial planning document introduced by the 2023 planning reform, gradually replacing SUIKZP.

The library checks adopted plans first, then falls back to projected/draft plans.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

pog = analyzer.pog()

print(pog.has_plan)       # True
print(pog.plan_name)      # "Plan ogolny Opola"
print(pog.is_draft)       # False (adopted) or True (projected)
print(pog.valid_from)     # "2025-12-18"
print(pog.document_url)   # URL to legal act
print(pog.infill_area)    # True if in building infill area
print(pog.downtown_area)  # True if in downtown area

print(pog.wms_url)        # WMS map URL

# Download map with plot boundary overlay (pip install plot-finder[viz])
png = analyzer.render_wms(pog.wms_url)

for zone in pog.zones:
    print(f"{zone.designation}: {zone.symbol} — {zone.symbol_name}")
    print(f"  Max height: {zone.max_building_height_m}m")
    print(f"  Max coverage: {zone.max_building_coverage_pct}%")
    print(f"  Min bio-active: {zone.min_bio_active_pct}%")
```

## Planning Zones

POG defines 13 zone types (strefy planistyczne):

| Symbol | Zone Name |
|--------|-----------|
| `SW` | Multi-family residential (wielofunkcyjna z zabudowa wielorodzinna) |
| `SJ` | Single-family residential (wielofunkcyjna z zabudowa jednorodzinna) |
| `SZ` | Farm-based development (wielofunkcyjna z zabudowa zagrodowa) |
| `SU` | Service zone (uslugowa) |
| `SH` | Large-format retail (handlu wielkopowierzchniowego) |
| `SP` | Economic/Industrial zone (gospodarcza) |
| `SR` | Agricultural production (produkcji rolniczej) |
| `SI` | Infrastructure (infrastrukturalna) |
| `SN` | Green space and recreation (zieleni i rekreacji) |
| `SC` | Cemetery (cmentarzy) |
| `SG` | Mining (gornicza) |
| `SO` | Open zone (otwarta) |
| `SK` | Transportation (komunikacyjna) |

## How It Works

1. Computes the plot centroid in EPSG:2180
2. Sends `GetFeatureInfo` to the **adopted** POG service (`PlanyOgolneGmin`)
3. If no adopted plan found, falls back to the **projected** POG service (`ProjektowanePlanyOgolneGmin`)
4. Parses GML response for zones, building parameters, and plan metadata
5. Checks for building infill areas (`obszarUzupelnieniaZabudowy`) and downtown areas (`obszarZabSrodmiejskiej`)

## POG Model

| Field | Type | Description |
|-------|------|-------------|
| `has_plan` | `bool` | Whether a POG exists for this location |
| `plan_name` | `str \| None` | Plan title |
| `valid_from` | `str \| None` | Date the plan became valid |
| `document_url` | `str \| None` | URL to the legal act |
| `is_draft` | `bool` | `True` if this is a projected/draft plan |
| `zones` | `list[PlanZone]` | Planning zones at this location |
| `infill_area` | `bool` | Whether the plot is in a building infill area |
| `downtown_area` | `bool` | Whether the plot is in a downtown development area |
| `wms_url` | `str \| None` | WMS GetMap URL |

## PlanZone Model

| Field | Type | Description |
|-------|------|-------------|
| `designation` | `str \| None` | Zone designation (e.g. "63SW") |
| `symbol` | `str \| None` | Zone type code (e.g. "SW") |
| `symbol_name` | `str \| None` | Human-readable zone name |
| `valid_from` | `str \| None` | Zone validity date |
| `max_building_intensity` | `float \| None` | Max above-ground building intensity |
| `max_building_coverage_pct` | `float \| None` | Max building coverage (%) |
| `max_building_height_m` | `float \| None` | Max building height (meters) |
| `min_bio_active_pct` | `float \| None` | Min biologically active surface (%) |

---
