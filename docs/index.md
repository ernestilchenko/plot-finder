# plot-finder

> Python library to find Polish land parcels and analyze their surroundings.

Query the [ULDK (GUGiK)](https://uldk.gugik.gov.pl/) API to get parcel data by TERYT ID or coordinates, then analyze nearby infrastructure using OpenStreetMap.

## Installation

=== "Base"

    ```bash
    pip install plot-finder
    ```

=== "With visualization"

    ```bash
    pip install plot-finder[viz]
    ```

=== "With AI analysis"

    ```bash
    pip install plot-finder[ai]
    ```

=== "With geo extras (MPZP, GUGiK)"

    ```bash
    pip install plot-finder[geo]
    ```

**Requirements:** Python 3.10+ | `pydantic` `httpx` `shapely` `pyproj`

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer, PlotReporter

# Find a parcel
plot = Plot(plot_id="141201_1.0001.6509")
print(plot.voivodeship)  # mazowieckie
print(plot.centroid)     # (x, y)

# Analyze surroundings
analyzer = PlotAnalyzer(plot, radius=3000)

for place in analyzer.education():
    print(f"{place.name} — {place.distance_m}m")

# Full report
report = PlotReporter(analyzer).report()
report.model_dump_json()
```

!!! tip "Async API"

    ```python
    import asyncio
    from plot_finder import create_plot_async, AsyncPlotAnalyzer, AsyncPlotReporter

    async def main():
        plot = await create_plot_async(plot_id="141201_1.0001.6509")
        async with AsyncPlotAnalyzer(plot, radius=3000) as a:
            report = await AsyncPlotReporter(a).report()

    asyncio.run(main())
    ```

!!! tip "Visualization"

    ```python
    # pip install plot-finder[viz]
    from plot_finder.visualizer import PlotVisualizer

    viz = PlotVisualizer(report)
    viz.save("map.html")  # interactive map
    viz.save("map.png")   # static image
    ```

## What's Inside

| Module | Description |
|--------|-------------|
| [Plot](plot.md) | Find parcels by TERYT ID, address, or coordinates |
| [PlotAnalyzer](analyzer.md) | Analyze surroundings — education, shops, transport, etc. |
| [Async API](async.md) | Async versions with concurrent HTTP (~5x faster) |
| [Climate](climate.md) | Temperature, precipitation, wind, frost/hot days |
| [Air Quality](air.md) | Air pollution data (OpenWeatherMap) |
| [Sunlight](sun.md) | Sunrise, sunset, daylight hours, seasonal data |
| [Noise](noise.md) | Noise levels from GDDKiA maps & OSM estimation |
| [Risks](risks.md) | Flood, seismic, soil, landslide, noise, mining risks |
| [MPZP](mpzp.md) | Local spatial development plan from Geoportal |
| [SUIKZP](suikzp.md) | Study of conditions and directions of spatial development |
| [POG](pog.md) | General Municipal Plan (zones, building parameters) |
| [KUIT](kuit.md) | Underground utility infrastructure (water, gas, power, etc.) |
| [Land Use](land_use.md) | Official land use classification (EGiB) |
| [GUGiK](gugik.md) | Spatial data services from GUGiK integration portal |
| [PlotReporter](report.md) | Full structured report in one call |
| [PlotVisualizer](visualizer.md) | Interactive HTML maps & static PNG images |
| [PlotAI](ai.md) | AI-powered analysis (OpenAI) |

## License

MIT — use it however you want.
