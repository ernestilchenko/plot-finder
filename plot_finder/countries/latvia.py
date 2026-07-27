from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import PlotNotFoundError, VZDError

_WFS_URL = (
    "https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/"
    "Zemes_vien_423_0p2RBZ/5cc09e19-a238-4a2e-8eac-3a05cefa050e"
)
_TYPE = "cp:CadastralParcel"


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
        "count": 1,
        "cql_filter": cql_filter,
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise VZDError(f"VZD WFS request failed: {exc}") from exc
    features = resp.json().get("features") or []
    return features[0] if features else None


class Latvia(BaseModel):
    """Latvia-specific parcel attributes, from Valsts zemes dienests (kadastrs.lv)."""

    territory_code: str | None = None
    group_code: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "LV"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 3059
    attributes: ClassVar[tuple[str, ...]] = ("territory_code", "group_code", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"label='{plot_id}'")
        else:
            lon, lat = _to_4326_lonlat(x, y, srid)
            feature = _wfs(f"INTERSECTS(geometry, POINT({lat} {lon}))")

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        label = feature["properties"].get("label")
        return {
            "plot_id": label,
            "geom_wkt": shape(feature["geometry"]).wkt,
            "geom_extent": None,
            "datasource": "Valsts zemes dienests (kadastrs.lv)",
            "territory_code": label[:4] if label else None,
            "group_code": label[4:7] if label and len(label) >= 7 else None,
            "parcel_number": label[7:] if label and len(label) > 7 else None,
        }
