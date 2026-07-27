from plot_finder.countries.cyprus import Cyprus
from plot_finder.countries.estonia import Estonia
from plot_finder.countries.france import France
from plot_finder.countries.latvia import Latvia
from plot_finder.countries.lithuania import Lithuania
from plot_finder.countries.netherlands import Netherlands
from plot_finder.countries.poland import Poland
from plot_finder.countries.spain import Spain
from plot_finder.countries.switzerland import Switzerland

REGISTRY = {
    c.code: c
    for c in (Poland, France, Spain, Netherlands, Switzerland, Estonia, Cyprus, Lithuania, Latvia)
}

__all__ = [
    "Poland",
    "France",
    "Spain",
    "Netherlands",
    "Switzerland",
    "Estonia",
    "Cyprus",
    "Lithuania",
    "Latvia",
    "REGISTRY",
]
