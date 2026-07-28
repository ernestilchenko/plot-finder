from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.countries._geo import to_4326
from plot_finder.exceptions import GURSError, PlotNotFoundError

_WFS_URL = "https://ipi.eprostor.gov.si/wfs-si-gurs-kn/wfs"
_PARCELS = "SI.GURS.KN:PARCELE"
_OBCINE = "SI.GURS.KN:PARCELE_X_RPE_OBCINE"
_WFS_SRID = 3794


def _to_3794():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", f"EPSG:{_WFS_SRID}", always_xy=True)


def _wfs(typename: str, cql_filter: str):
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": typename,
        "outputFormat": "application/json",
        "srsName": f"urn:ogc:def:crs:EPSG::{_WFS_SRID}",
        "count": 1,
        "cql_filter": cql_filter,
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, timeout=40, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise GURSError(f"GURS WFS request failed: {exc}") from exc
    features = resp.json().get("features") or []
    return features[0] if features else None


def _obcina(ko: int, parcel: str) -> str | None:
    try:
        feature = _wfs(_OBCINE, f"KO_ID={ko} AND ST_PARCELE='{parcel}'")
        return feature["properties"].get("RPE_OBCINE_NAZIV") if feature else None
    except GURSError:
        return None


class Slovenia(BaseModel):
    """Slovenia-specific parcel attributes, from GURS (e-prostor)."""

    ko_code: str | None = None
    ko_name: str | None = None
    municipality: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "SI"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 3794
    attributes: ClassVar[tuple[str, ...]] = ("ko_code", "ko_name", "municipality", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            ko, _, parcel = plot_id.replace(" ", "-").partition("-")
            feature = _wfs(_PARCELS, f"KO_ID={ko} AND ST_PARCELE='{parcel}'")
        else:
            east, north = (x, y) if srid == _WFS_SRID else _to_3794().transform(x, y)
            feature = _wfs(_PARCELS, f"INTERSECTS(GEOM, POINT({east} {north}))")

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature["properties"]
        ko_id = props.get("KO_ID")
        parcel = props.get("ST_PARCELE")
        geom = to_4326(shape(feature["geometry"]), _WFS_SRID)
        return {
            "plot_id": f"{ko_id}-{parcel}" if ko_id and parcel else plot_id,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "GURS (e-prostor)",
            "ko_code": str(ko_id) if ko_id is not None else None,
            "ko_name": props.get("NAZIV"),
            "municipality": _obcina(ko_id, parcel) if ko_id and parcel else None,
            "parcel_number": parcel,
        }
