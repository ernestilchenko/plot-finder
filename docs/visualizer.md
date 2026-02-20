# PlotVisualizer

Render a [PlotReport](report.md) as an interactive HTML map or a static PNG/JPG image.

> **Optional dependency** — not included in the base install.
> ```bash
> pip install plot-finder[viz]
> ```
> This installs `folium` (interactive maps) and `Pillow` (static images).

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer, PlotReporter
from plot_finder.visualizer import PlotVisualizer

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=2000)
report = PlotReporter(analyzer).report()

viz = PlotVisualizer(report)

viz.save("map.html")   # interactive map
viz.save("map.png")    # static image
```

---

## Constructor

```python
PlotVisualizer(report, *, colors=None, plot_color="red")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report` | `PlotReport` | required | Report to visualize |
| `colors` | `dict[str, str] \| None` | `None` | Override category colours |
| `plot_color` | `str` | `"red"` | Centre marker and radius circle colour |

### Default Category Colours

| Category | Colour | Icon (HTML) |
|----------|--------|-------------|
| `education` | blue | graduation-cap |
| `finance` | green | university |
| `transport` | orange | bus |
| `infrastructure` | purple | building |
| `parks` | darkgreen | tree |
| `water` | cadetblue | tint |

Override any of them:

```python
viz = PlotVisualizer(report, colors={
    "education": "#1f77b4",
    "parks": "#2ca02c",
    "transport": "darkred",
})
```

---

## Methods

### `map() -> folium.Map`

Returns an interactive [folium](https://python-visualization.github.io/folium/) map with:

- Red centre marker with plot ID popup
- Dashed circle showing search radius
- Colour-coded markers per category (as FeatureGroups)
- LayerControl to toggle categories on/off
- Popups with name, kind, distance, walk/bike/car time

```python
m = viz.map()
m.save("map.html")

# Or use in Jupyter
m
```

**Requires:** `folium`

### `image(width=800, height=600, zoom=None, marker_radius=6) -> PIL.Image.Image`

Renders a static map image from OpenStreetMap tiles.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | `int` | `800` | Image width in pixels |
| `height` | `int` | `600` | Image height in pixels |
| `zoom` | `int \| None` | `None` | Zoom level (1–18). Auto-detected from radius if `None` |
| `marker_radius` | `int` | `6` | Size of place markers in pixels |

```python
img = viz.image(width=1200, height=800)
img.save("map.png")

# Custom zoom
img = viz.image(zoom=14)

# Bigger markers
img = viz.image(marker_radius=10)
```

The image contains:

- OpenStreetMap base tiles
- Circle outline showing search radius
- Colour-coded dot markers per category
- Larger centre marker for the plot

**Requires:** `Pillow`

### `save(path)`

Auto-detects format by file extension:

| Extension | Output |
|-----------|--------|
| `.html` | Interactive folium map |
| `.png` | Static PNG image |
| `.jpg` / `.jpeg` | Static JPEG image |

```python
viz.save("map.html")   # folium
viz.save("map.png")    # PIL → PNG
viz.save("map.jpg")    # PIL → JPEG
```

---

## Colour Reference

Colours accepted by `image()` (PIL) — any CSS colour name or hex string:

```python
"red", "#FF0000", "darkgreen", "#2ca02c", "cornflowerblue"
```

Colours accepted by `map()` (folium icons) — limited set:

```
red, blue, green, purple, orange, darkred, darkblue,
darkgreen, cadetblue, darkpurple, pink, lightblue,
lightgreen, beige, white, lightgray, gray, black, lightred
```

> For best results, use colours that work in both systems (named colours like `red`, `blue`, `green`, `purple`, `orange`, `darkgreen`).

---

## Examples

### Custom colours

```python
viz = PlotVisualizer(
    report,
    colors={"education": "darkblue", "transport": "darkred"},
    plot_color="black",
)
viz.save("custom.png")
```

### High-resolution image

```python
img = viz.image(width=1920, height=1080, zoom=16, marker_radius=8)
img.save("hd.png")
```

### Folium in Jupyter

```python
viz.map()  # displays inline
```

---
