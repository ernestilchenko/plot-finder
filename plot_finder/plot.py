from typing import Any, Literal

import httpx
import shapely.geometry
import shapely.wkt
from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from plot_finder.countries import REGISTRY
from plot_finder.exceptions import AddressNotFoundError, GeocodeError
from plot_finder.utils import reproject

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class Plot(BaseModel):
    """A land parcel. ``country`` selects the cadastre and the extra attributes.

    Input coordinates are always ``lon``/``lat`` (EPSG:4326). Geometry is returned
    as ``geojson`` in EPSG:4326 by default; set ``srid`` for another output CRS.
    Country-specific attributes (``voivodeship`` for PL, ``department`` for FR,
    ...) are sourced from the matching class in :mod:`plot_finder.countries` and
    exposed directly on the plot::

        Plot(country="PL", plot_id="141201_1.0001.6509").voivodeship
        Plot(country="FR", x=-0.5792, y=44.8378).department
    """

    model_config = ConfigDict(extra="allow")

    country: Literal["PL", "FR", "ES", "NL", "CH", "EE", "CY", "LT", "LV", "PT", "SI", "IT", "DE", "NO", "DK", "BE"]
    plot_id: str | None = None
    address: str | None = None
    x: float | None = None
    y: float | None = None
    srid: int = 4326
    geojson: dict[str, Any] | None = None
    datasource: str | None = None

    def _geom(self):
        return shapely.geometry.shape(self.geojson) if self.geojson else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float | None:
        geom = self._geom()
        if geom is None:
            return None
        if self.srid != 4326:
            geom = reproject(geom, self.srid, 4326)
        from pyproj import Geod
        area, _ = Geod(ellps="WGS84").geometry_area_perimeter(geom)
        return round(abs(area), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def centroid(self) -> tuple[float, float] | None:
        geom = self._geom()
        if geom is None:
            return None
        return geom.centroid.x, geom.centroid.y

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bbox(self) -> tuple[float, float, float, float] | None:
        geom = self._geom()
        return geom.bounds if geom is not None else None

    @model_validator(mode="after")
    def _auto_fetch(self) -> "Plot":
        country = REGISTRY[self.country]
        if self.geojson is not None:
            return self
        if self.address and not self.plot_id and self.x is None:
            self._geocode()
        if not self.plot_id and self.x is None:
            raise ValueError("Provide 'plot_id', 'address', or both 'x' and 'y'")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")

        data = country.fetch(self.plot_id, self.x, self.y, country.default_srid)
        if data.get("plot_id") is not None:
            self.plot_id = data["plot_id"]
        if data.get("datasource") is not None:
            self.datasource = data["datasource"]

        if data.get("geom_wkt"):
            geom = shapely.wkt.loads(data["geom_wkt"])
            if self.srid != 4326:
                geom = reproject(geom, 4326, self.srid)
            self.geojson = shapely.geometry.mapping(geom)

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
