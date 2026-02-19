# PlotAI

AI-powered plot analysis using OpenAI. Ask questions, get ratings, and receive natural language summaries of any [PlotReport](report.md).

> **Optional dependency** — not included in the base install.
> ```bash
> pip install plot-finder[ai]
> ```
> This installs `openai`.

---

## Quick Start

```python
from plot_finder import Plot, PlotAnalyzer, PlotReporter
from plot_finder.ai import PlotAI

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=2000)
report = PlotReporter(analyzer).report()

ai = PlotAI(report, api_key="sk-...")
print(ai.summary())
```

---

## Constructor

```python
PlotAI(report, *, api_key, model="gpt-4o-mini")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report` | `PlotReport` | required | Report to analyze |
| `api_key` | `str` | required | OpenAI API key |
| `model` | `str` | `"gpt-4o-mini"` | OpenAI model to use |

---

## Methods

All methods return `str`.

### `summary()`

Natural language summary of the plot and surroundings — location, nearby infrastructure, transport, nature, air quality, and sunlight.

```python
print(ai.summary())
# "The plot 141201_1.0001.6509 is located in central Warsaw..."
```

### `rate(purpose="living")`

Rate the plot 1–10 for a specific purpose with explanation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `purpose` | `str` | `"living"` | Purpose to rate for |

```python
print(ai.rate())                        # living (default)
print(ai.rate(purpose="investment"))    # investment
print(ai.rate(purpose="farming"))       # farming
```

### `advantages()`

Key advantages of this location based on the report data.

```python
print(ai.advantages())
# "1. Excellent transport links — 3 bus stops within 500m..."
```

### `disadvantages()`

Key disadvantages and risks of this location.

```python
print(ai.disadvantages())
# "1. No schools within walking distance..."
```

### `ask(question)`

Freeform Q&A about the plot.

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | Any question about the plot |

```python
print(ai.ask("Is this a good place for a family with kids?"))
print(ai.ask("What are the nearest parks?"))
print(ai.ask("How is the air quality?"))
```

---

## Model Selection

The default model is `gpt-4o-mini` — fast and cheap. For more detailed analysis, use a larger model:

```python
ai = PlotAI(report, api_key="sk-...", model="gpt-4o")
```

---

## Examples

### Full analysis

```python
from plot_finder import Plot, PlotAnalyzer, PlotReporter
from plot_finder.ai import PlotAI

plot = Plot(plot_id="141201_1.0001.6509")
analyzer = PlotAnalyzer(plot, radius=3000)
report = PlotReporter(analyzer).report()

ai = PlotAI(report, api_key="sk-...")

print("=== Summary ===")
print(ai.summary())

print("\n=== Rating (living) ===")
print(ai.rate())

print("\n=== Rating (investment) ===")
print(ai.rate(purpose="investment"))

print("\n=== Advantages ===")
print(ai.advantages())

print("\n=== Disadvantages ===")
print(ai.disadvantages())

print("\n=== Q&A ===")
print(ai.ask("Is this a good place for a family with kids?"))
```

### Using environment variable for API key

```python
import os
from plot_finder.ai import PlotAI

ai = PlotAI(report, api_key=os.environ["OPENAI_API_KEY"])
```

---

[Back to README](../README.md) | [Prev: Visualizer](visualizer.md) | [Next: API Reference](api.md)
