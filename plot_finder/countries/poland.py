from typing import ClassVar

from pydantic import BaseModel

from plot_finder.exceptions import PlotNotFoundError, ULDKError
from plot_finder.utils import get

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
    result: dict = {}
    for name, value in zip(_RESULT_FIELDS.split(","), parts):
        val = value.strip() or None
        result["plot_id" if name == "teryt" else name] = val

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
        return {"request": "GetParcelByXY", "xy": xy, "result": _RESULT_FIELDS, "srid": str(srid)}
    return {"request": "GetParcelById", "id": plot_id, "result": _RESULT_FIELDS, "srid": str(srid)}


class Poland(BaseModel):
    """Poland-specific parcel attributes, from the ULDK (GUGiK) API."""

    voivodeship: str | None = None
    county: str | None = None
    commune: str | None = None
    region: str | None = None
    parcel: str | None = None

    code: ClassVar[str] = "PL"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("voivodeship", "county", "commune", "region", "parcel")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        resp = get(_ULDK_URL, ULDKError, params=_build_uldk_params(plot_id, x, y, srid), timeout=30)
        return _parse_uldk_response(resp.text, plot_id, x, y)
