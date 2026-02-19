from typing import Any

import httpx
import shapely.wkt
from pydantic import BaseModel, computed_field, model_validator

from plot_finder.exceptions import PlotNotFoundError, ULDKError

_ULDK_URL = "https://uldk.gugik.gov.pl/"
_RESULT_FIELDS = "teryt,voivodeship,county,commune,region,parcel,geom_wkt,geom_extent,datasource"


class Plot(BaseModel):
    plot_id: str | None = None
    x: float | None = None
    y: float | None = None
    voivodeship: str | None = None
    county: str | None = None
    commune: str | None = None
    region: str | None = None
    parcel: str | None = None
    srid: int = 2180
    geom_wkt: str | None = None
    geom_extent: str | None = None
    datasource: str | None = None

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
        if self.voivodeship is not None:
            return self
        if not self.plot_id and self.x is None:
            raise ValueError("Either 'plot' or both 'x' and 'y' must be provided")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")
        self._fetch()
        return self

    def _fetch(self) -> None:
        if self.x is not None:
            xy = f"{self.x},{self.y}"
            if self.srid != 2180:
                xy += f",{self.srid}"
            params = {
                "request": "GetParcelByXY",
                "xy": xy,
                "result": _RESULT_FIELDS,
                "srid": str(self.srid),
            }
        else:
            params = {
                "request": "GetParcelById",
                "id": self.plot_id,
                "result": _RESULT_FIELDS,
                "srid": str(self.srid),
            }

        try:
            resp = httpx.get(_ULDK_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ULDKError(f"HTTP request failed: {exc}") from exc

        lines = resp.text.strip().splitlines()
        if not lines:
            raise ULDKError("Empty response from ULDK API")

        status = lines[0].strip()
        if status.startswith("-1") or len(lines) < 2:
            query = f"xy={self.x},{self.y}" if self.x is not None else self.plot_id
            raise PlotNotFoundError(f"Parcel not found: {query}")

        parts = lines[1].split("|")
        field_names = _RESULT_FIELDS.split(",")
        for name, value in zip(field_names, parts):
            val = value.strip() or None
            if name == "teryt":
                self.plot_id = val
            else:
                setattr(self, name, val)

        if self.geom_wkt and ";" in self.geom_wkt:
            _, wkt = self.geom_wkt.split(";", 1)
            self.geom_wkt = wkt
