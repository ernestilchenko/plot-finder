# Noise

Estimate noise levels at the plot location using official GDDKiA strategic noise maps, with OpenStreetMap fallback estimation.

---

## Usage

```python
from plot_finder import Plot, PlotAnalyzer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot)

noise = analyzer.noise()

print(noise.noise_level_db)  # 52.0
print(noise.quality)         # "Niski"
print(noise.level)           # "low"
print(noise.color)           # "lightgreen"
print(noise.data_source)     # "GDDKiA" or "OpenStreetMap (szacunkowy)"

for src in noise.sources:
    print(f"{src.type}: {src.name} — {src.distance_km} km, {src.impact_db} dB")
```

## How It Works

1. **GDDKiA WMS** — queries the official strategic noise map (LDWN indicator) from Geoportal. Tries the voivodeship-specific layer first, then falls back to major voivodeships.
2. **OSM fallback** — if no GDDKiA data is available, estimates noise based on distance to motorways, railways, airports, and industrial zones from OpenStreetMap.

## Noise Model

| Field | Type | Description |
|-------|------|-------------|
| `noise_level_db` | `float` | Estimated noise level in decibels |
| `quality` | `str` | Polish quality label (Bardzo niski / Niski / Umiarkowany / Wysoki / Bardzo wysoki) |
| `level` | `str` | English level key (very_low / low / moderate / high / very_high) |
| `description` | `str` | Polish description |
| `color` | `str` | Indicator color (green / lightgreen / yellow / orange / red) |
| `sources` | `list[NoiseSource]` | Detected noise sources |
| `data_source` | `str` | Data origin (GDDKiA or OpenStreetMap) |

## NoiseSource Model

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Source type (e.g. Autostrada, Linia kolejowa) |
| `name` | `str` | Source name from map data |
| `distance_km` | `float` | Distance from plot in km |
| `impact_db` | `float` | Estimated noise impact in dB |
| `lat` | `float` | Latitude |
| `lon` | `float` | Longitude |

## Noise Levels

| Range | Quality | Level | Color |
|-------|---------|-------|-------|
| < 45 dB | Bardzo niski | very_low | green |
| 45–55 dB | Niski | low | lightgreen |
| 55–65 dB | Umiarkowany | moderate | yellow |
| 65–75 dB | Wysoki | high | orange |
| > 75 dB | Bardzo wysoki | very_high | red |

---
