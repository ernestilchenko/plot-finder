from typing import ClassVar

import httpx

from plot_finder.base import BasePlot
from plot_finder.exceptions import PlotNotFoundError, ULDKError

_ULDK_URL = "https://uldk.gugik.gov.pl/"
_RESULT_FIELDS = "teryt,voivodeship,county,commune,region,parcel,geom_wkt,geom_extent,datasource"


def _parse_uldk_response(text: str, plot_id: str | None, x: float | None, y: float | None) -> dict:
    """Parse an ULDK API response into a dict of field values."""
    lines = text.strip().splitlines()
    if not lines:
        raise ULDKError("Empty response from ULDK API")

    status = lines[0].strip()
    if status.startswith("-1") or len(lines) < 2:
        query = f"xy={x},{y}" if x is not None else plot_id
        raise PlotNotFoundError(f"Parcel not found: {query}")

    parts = lines[1].split("|")
    field_names = _RESULT_FIELDS.split(",")
    result: dict = {}
    for name, value in zip(field_names, parts):
        val = value.strip() or None
        if name == "teryt":
            result["plot_id"] = val
        else:
            result[name] = val

    if result.get("geom_wkt") and ";" in result["geom_wkt"]:
        _, wkt = result["geom_wkt"].split(";", 1)
        result["geom_wkt"] = wkt

    return result


def _build_uldk_params(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
    """Build ULDK API request params."""
    if x is not None:
        xy = f"{x},{y}"
        if srid != 2180:
            xy += f",{srid}"
        return {
            "request": "GetParcelByXY",
            "xy": xy,
            "result": _RESULT_FIELDS,
            "srid": str(srid),
        }
    return {
        "request": "GetParcelById",
        "id": plot_id,
        "result": _RESULT_FIELDS,
        "srid": str(srid),
    }


class PolandPlot(BasePlot):
    """A land parcel in Poland, from the ULDK (GUGiK) API.

    ``plot_id`` is the TERYT identifier; coordinates are in EPSG:2180 by default.
    """

    voivodeship: str | None = None
    county: str | None = None
    commune: str | None = None
    region: str | None = None
    parcel: str | None = None

    srid: int = 2180
    _area_crs: ClassVar[int] = 2180

    def _fetch(self) -> None:
        params = _build_uldk_params(self.plot_id, self.x, self.y, self.srid)
        try:
            resp = httpx.get(_ULDK_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ULDKError(f"HTTP request failed: {exc}") from exc

        fields = _parse_uldk_response(resp.text, self.plot_id, self.x, self.y)
        for name, value in fields.items():
            setattr(self, name, value)
