from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import PlotNotFoundError, RCError

_WFS_URL = "https://www.inspire-geoportal.lt/geoserver/cp/wfs"
_TYPE = "cp:CP.CadastralParcel"


def _to_4326_lonlat(x: float, y: float, srid: int) -> tuple[float, float]:
    if srid == 4326:
        return x, y
    from pyproj import Transformer
    return Transformer.from_crs(f"EPSG:{srid}", "EPSG:4326", always_xy=True).transform(x, y)


def _wfs(cql_filter: str):
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": _TYPE,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "count": 1,
        "CQL_FILTER": cql_filter,
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise RCError(f"geoportal.lt WFS request failed: {exc}") from exc
    features = resp.json().get("features") or []
    return features[0] if features else None


class Lithuania(BaseModel):
    """Lithuania-specific parcel attributes, from Registrų centras (geoportal.lt)."""

    cadastral_zone: str | None = None
    municipality_code: str | None = None
    purpose: str | None = None

    code: ClassVar[str] = "LT"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 3346
    attributes: ClassVar[tuple[str, ...]] = ("cadastral_zone", "municipality_code", "purpose")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"label='{plot_id}'")
        else:
            lon, lat = _to_4326_lonlat(x, y, srid)
            feature = _wfs(f"INTERSECTS(geometry, POINT({lat} {lon}))")

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature["properties"]
        label = props.get("label")
        zone = label.split("/")[0] if label and "/" in label else None
        href = props.get("administrativeunit_href") or ""
        municipality_code = href.split("municipality_")[-1] if "municipality_" in href else None
        description = props.get("description") or ""
        purpose = description.split(":", 1)[1].strip() if ":" in description else (description or None)

        return {
            "plot_id": label,
            "geom_wkt": shape(feature["geometry"]).wkt,
            "geom_extent": None,
            "datasource": "Registrų centras (geoportal.lt)",
            "cadastral_zone": zone,
            "municipality_code": municipality_code,
            "purpose": purpose,
        }
