from typing import Any, Literal

import httpx
import shapely.geometry
import shapely.wkt
from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from plot_finder.countries import REGISTRY
from plot_finder.countries._geo import reproject
from plot_finder.exceptions import AddressNotFoundError, GeocodeError

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_COMMON = ("plot_id", "geom_wkt", "geom_extent", "datasource")


class Plot(BaseModel):
    """A land parcel. ``country`` selects the cadastre and the extra attributes.

    Geometry is returned in EPSG:4326 by default; set ``srid`` for another output
    CRS. Input coordinates are read in the country's native CRS unless ``in_srid``
    is given. Country-specific attributes (``voivodeship`` for PL, ``department``
    for FR, ...) are sourced from the matching class in
    :mod:`plot_finder.countries` and exposed directly on the plot::

        Plot(country="PL", plot_id="141201_1.0001.6509").voivodeship
        Plot(country="FR", x=-0.5792, y=44.8378).department
    """

    model_config = ConfigDict(extra="allow")

    country: Literal["PL", "FR", "ES", "NL", "CH", "EE", "CY", "LT", "LV", "PT"]
    plot_id: str | None = None
    address: str | None = None
    x: float | None = None
    y: float | None = None
    srid: int = 4326
    in_srid: int | None = None
    geom_wkt: str | None = None
    geom_extent: str | None = None
    datasource: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return round(reproject(geom, self.srid, REGISTRY[self.country].area_crs).area, 2)

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
        return shapely.geometry.mapping(shapely.wkt.loads(self.geom_wkt))

    @model_validator(mode="after")
    def _auto_fetch(self) -> "Plot":
        country = REGISTRY[self.country]
        if self.geom_wkt is not None:
            return self
        if self.in_srid is None:
            self.in_srid = country.default_srid
        if self.address and not self.plot_id and self.x is None:
            self._geocode()
        if not self.plot_id and self.x is None:
            raise ValueError("Provide 'plot_id', 'address', or both 'x' and 'y'")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")

        data = country.fetch(self.plot_id, self.x, self.y, self.in_srid)

        for key in _COMMON:
            if data.get(key) is not None:
                setattr(self, key, data[key])

        if self.srid != 4326 and self.geom_wkt:
            self.geom_wkt = reproject(shapely.wkt.loads(self.geom_wkt), 4326, self.srid).wkt

        details = country(**{name: data.get(name) for name in country.attributes})
        for name in country.attributes:
            setattr(self, name, getattr(details, name))
        return self

    def _geocode(self) -> None:
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
        self.in_srid = 4326
