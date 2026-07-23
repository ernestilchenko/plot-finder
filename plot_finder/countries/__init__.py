from plot_finder.countries.france import France
from plot_finder.countries.poland import Poland
from plot_finder.countries.spain import Spain

# Registry: country code -> attribute/fetcher class.
REGISTRY = {Poland.code: Poland, France.code: France, Spain.code: Spain}

__all__ = ["Poland", "France", "Spain", "REGISTRY"]
