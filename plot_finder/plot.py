from typing import Any, Literal

import httpx
import shapely.geometry
import shapely.wkt
from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from plot_finder.countries import REGISTRY
from plot_finder.exceptions import AddressNotFoundError, GeocodeError

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Fields shared by every country, populated from the fetch result.
_COMMON = ("plot_id", "geom_wkt", "geom_extent", "datasource")


class Plot(BaseModel):
    """A land parcel. ``country`` selects the cadastre and the extra attributes.

    Country-specific attributes (``voivodeship`` for PL, ``department`` for FR,
    ...) are sourced from the matching class in :mod:`plot_finder.countries` and
    exposed directly on the plot::

        Plot(country="PL", plot_id="141201_1.0001.6509").voivodeship
        Plot(country="FR", x=-0.5792, y=44.8378).department
    """

    model_config = ConfigDict(extra="allow")

    country: Literal["PL", "FR", "ES"]
    plot_id: str | None = None
    address: str | None = None
    x: float | None = None
    y: float | None = None
    srid: int | None = None
    geom_wkt: str | None = None
    geom_extent: str | None = None
    datasource: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float | None:
        """Area in m². Transforms to the country's metric CRS if needed."""
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        target = REGISTRY[self.country].area_crs
        if self.srid != target:
            from pyproj import Transformer
            from shapely.ops import transform
            t = Transformer.from_crs(f"EPSG:{self.srid}", f"EPSG:{target}", always_xy=True)
            geom = transform(t.transform, geom)
        return round(geom.area, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def centroid(self) -> tuple[float, float] | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return geom.centroid.x, geom.centroid.y

    @computed_field  # type: ignore[prop-decorator]
    @property
    def geojson(self) -> dict[str, Any] | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return shapely.geometry.mapping(geom)

    @model_validator(mode="after")
    def _auto_fetch(self) -> "Plot":
        country = REGISTRY[self.country]
        if self.geom_wkt is not None:
            return self  # already populated (e.g. re-validated from a dump)
        if self.srid is None:
            self.srid = country.default_srid
        if self.address and not self.plot_id and self.x is None:
            self._geocode()
        if not self.plot_id and self.x is None:
            raise ValueError("Provide 'plot_id', 'address', or both 'x' and 'y'")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")

        data = country.fetch(self.plot_id, self.x, self.y, self.srid)

        for key in _COMMON:
            if data.get(key) is not None:
                setattr(self, key, data[key])

        # Country-specific attributes are sourced from the country class, then
        # exposed flat on the plot.
        details = country(**{name: data.get(name) for name in country.attributes})
        for name in country.attributes:
            setattr(self, name, getattr(details, name))
        return self

    def _geocode(self) -> None:
        """Resolve ``address`` to lon/lat via OpenStreetMap Nominatim."""
        params = {"q": self.address, "format": "json", "limit": 1}
        headers = {"User-Agent": "plot-finder/1.0"}
        try:
            resp = httpx.get(_NOMINATIM_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodeError(f"Geocoding request failed: {exc}") from exc

        results = resp.json()
        if not results:
            raise AddressNotFoundError(f"No results for address: {self.address}")

        self.y = float(results[0]["lat"])
        self.x = float(results[0]["lon"])
        self.srid = 4326
