from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import DAWAError, PlotNotFoundError

_BASE = "https://api.dataforsyningen.dk/jordstykker"


def _get(url: str, params: dict) -> dict | None:
    try:
        resp = httpx.get(url, params=params, timeout=30, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise DAWAError(f"DAWA request failed: {exc}") from exc
    if resp.status_code == 404:
        return None
    try:
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        raise DAWAError(f"DAWA request failed: {exc}") from exc
    except ValueError as exc:
        raise DAWAError(f"Invalid JSON from DAWA: {exc}") from exc


class Denmark(BaseModel):
    """Denmark-specific parcel attributes, from DAWA / SDFI (Matriklen)."""

    municipality: str | None = None
    ejerlav: str | None = None
    matrikelnr: str | None = None

    code: ClassVar[str] = "DK"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("municipality", "ejerlav", "matrikelnr")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            ejerlavkode, _, matrikelnr = plot_id.partition("-")
            feature = _get(f"{_BASE}/{ejerlavkode}/{matrikelnr}", {"srid": srid, "format": "geojson"})
        else:
            feature = _get(f"{_BASE}/reverse", {"x": x, "y": y, "srid": srid, "format": "geojson"})

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature["properties"]
        geom = shape(feature["geometry"])
        code = props.get("ejerlavkode")
        matrikelnr = props.get("matrikelnr")
        return {
            "plot_id": f"{code}-{matrikelnr}" if code and matrikelnr else plot_id,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "DAWA / SDFI (Matriklen)",
            "municipality": props.get("kommunenavn"),
            "ejerlav": props.get("ejerlavnavn"),
            "matrikelnr": matrikelnr,
        }
