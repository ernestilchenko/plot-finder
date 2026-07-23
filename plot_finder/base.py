from typing import Any, ClassVar

import httpx
import shapely.geometry
import shapely.wkt
from pydantic import BaseModel, computed_field, model_validator

from plot_finder.exceptions import AddressNotFoundError, GeocodeError

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class BasePlot(BaseModel):
    """Shared parcel fields, geometry helpers and fetch orchestration.

    Country-specific subclasses (:class:`~plot_finder.poland.PolandPlot`,
    :class:`~plot_finder.france.FrancePlot`) add their own descriptive fields
    and implement :meth:`_fetch`.
    """

    plot_id: str | None = None
    address: str | None = None
    x: float | None = None
    y: float | None = None
    srid: int = 2180
    geom_wkt: str | None = None
    geom_extent: str | None = None
    datasource: str | None = None

    # Metric CRS used to compute the area; overridden per country.
    _area_crs: ClassVar[int] = 2180

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float | None:
        """Area in m². Transforms to the country's metric CRS if needed."""
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        if self.srid != self._area_crs:
            from pyproj import Transformer
            from shapely.ops import transform
            t = Transformer.from_crs(f"EPSG:{self.srid}", f"EPSG:{self._area_crs}", always_xy=True)
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
    def _auto_fetch(self) -> "BasePlot":
        if self.geom_wkt is not None:
            return self
        if self.address and not self.plot_id and self.x is None:
            self._geocode()
        if not self.plot_id and self.x is None:
            raise ValueError("Either 'plot_id', 'address', or both 'x' and 'y' must be provided")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")
        self._fetch()
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

    def _fetch(self) -> None:
        """Fetch parcel data from the country's cadastre. Overridden per country."""
        raise NotImplementedError
