from plot_finder.countries.france import France
from plot_finder.countries.poland import Poland

# Registry: country code -> attribute/fetcher class.
REGISTRY = {Poland.code: Poland, France.code: France}

__all__ = ["Poland", "France", "REGISTRY"]
