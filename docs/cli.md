# CLI

Command-line interface for quick plot analysis without writing code.

```bash
pip install plot-finder
```

---

## Usage

```
plot-finder <command> [options]
```

Running `plot-finder` without arguments shows the banner and help:

```
           __      __        _____           __
    ____  / /___  / /_      / __(_)___  ____/ /__  _____
   / __ \/ / __ \/ __/_____/ /_/ / __ \/ __  / _ \/ ___/
  / /_/ / / /_/ / /_/_____/ __/ / / / / /_/ /  __/ /
 / .___/_/\____/\__/     /_/ /_/_/ /_/\__,_/\___/_/
/_/
```

Also available as `python -m plot_finder <command> ...`

---

## Commands

### `analyze` — Full report

```bash
plot-finder analyze 141201_1.0001.6509
plot-finder analyze 141201_1.0001.6509 --radius 2000
plot-finder analyze 141201_1.0001.6509 --json
plot-finder analyze 141201_1.0001.6509 --openweather-key YOUR_KEY
```

| Option | Description |
|--------|-------------|
| `--radius N` | Search radius in meters (default: 1000) |
| `--json` | Output raw JSON |
| `--openweather-key KEY` | OpenWeatherMap API key for air quality |

### `search` — Find a plot

```bash
plot-finder search --address "Warszawa, Marszalkowska 1"
plot-finder search --plot-id 141201_1.0001.6509
plot-finder search --x 21.0 --y 52.2
plot-finder search --address "Krakow, Rynek 1" --json
```

| Option | Description |
|--------|-------------|
| `--address` | Street address (geocoded via Nominatim) |
| `--plot-id` | TERYT parcel ID |
| `--x`, `--y` | Coordinates |
| `--json` | Output raw JSON |

### `places` — Nearby places

```bash
plot-finder places 141201_1.0001.6509
plot-finder places 141201_1.0001.6509 --category education
plot-finder places 141201_1.0001.6509 --radius 3000 --json
```

| Option | Description |
|--------|-------------|
| `--radius N` | Search radius in meters (default: 1000) |
| `--category C` | Filter: education, finance, transport, infrastructure, green_areas, water, nuisances |
| `--json` | Output raw JSON |

### `elevation` — Elevation, slope, aspect

```bash
plot-finder elevation 141201_1.0001.6509
plot-finder elevation 141201_1.0001.6509 --json
```

### `climate` — Climate data

```bash
plot-finder climate 141201_1.0001.6509
plot-finder climate 141201_1.0001.6509 --json
```

### `sunlight` — Sunrise, sunset, daylight

```bash
plot-finder sunlight 141201_1.0001.6509
plot-finder sunlight 141201_1.0001.6509 --date 2025-06-21
plot-finder sunlight 141201_1.0001.6509 --json
```

| Option | Description |
|--------|-------------|
| `--date YYYY-MM-DD` | Date to calculate for (default: today) |
| `--json` | Output raw JSON |

### `noise` — Noise level

```bash
plot-finder noise 141201_1.0001.6509
plot-finder noise 141201_1.0001.6509 --json
```

### `risks` — Environmental risks

```bash
plot-finder risks 141201_1.0001.6509
plot-finder risks 141201_1.0001.6509 --json
```

---

## JSON Output

All commands support `--json` for machine-readable output, useful for piping:

```bash
plot-finder elevation 141201_1.0001.6509 --json | jq '.elevation_m'
plot-finder analyze 141201_1.0001.6509 --json > report.json
```
