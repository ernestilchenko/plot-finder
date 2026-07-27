from plot_finder.countries.france import France
from plot_finder.countries.netherlands import Netherlands
from plot_finder.countries.poland import Poland
from plot_finder.countries.spain import Spain

# Registry: country code -> attribute/fetcher class.
REGISTRY = {c.code: c for c in (Poland, France, Spain, Netherlands)}

__all__ = ["Poland", "France", "Spain", "Netherlands", "REGISTRY"]
