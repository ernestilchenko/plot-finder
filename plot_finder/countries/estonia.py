from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.countries._geo import to_4326
from plot_finder.exceptions import MaaametError, PlotNotFoundError

_WFS_URL = "https://inspire.geoportaal.ee/geoserver/wfs"
_INADS_URL = "https://inaadress.maaamet.ee/inaadress/gazetteer"
_TYPE = "CP_katastriyksused:CP.CadastralParcel"
_WFS_SRID = 3301


def _to_3301():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", "EPSG:3301", always_xy=True)


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
        resp = httpx.get(_WFS_URL, params=params, timeout=40, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise MaaametError(f"Maa-amet WFS request failed: {exc}") from exc
    features = resp.json().get("features") or []
    return features[0] if features else None


def _inads(tunnus: str) -> tuple[str | None, str | None, str | None]:
    try:
        resp = httpx.get(
            _INADS_URL,
            params={"address": tunnus, "features": "KATASTRIYKSUS", "results": 1},
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json().get("addresses") or []
        if items:
            a = items[0]
            return a.get("maakond"), a.get("omavalitsus"), a.get("asustusyksus")
    except (httpx.HTTPError, ValueError):
        pass
    return (None, None, None)


class Estonia(BaseModel):
    """Estonia-specific parcel attributes, from the Maa-amet (Land Board)."""

    county: str | None = None
    municipality: str | None = None
    settlement: str | None = None

    code: ClassVar[str] = "EE"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 3301
    attributes: ClassVar[tuple[str, ...]] = ("county", "municipality", "settlement")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"nationalcadastralreference='{plot_id}'")
        else:
            east, north = (x, y) if srid == _WFS_SRID else _to_3301().transform(x, y)
            feature = _wfs(f"INTERSECTS(geom, POINT({north} {east}))")

        if feature is None:
            query = plot_id or f"xy={x},{y}"
            raise PlotNotFoundError(f"Parcel not found: {query}")

        props = feature["properties"]
        tunnus = props.get("nationalcadastralreference")
        geom = to_4326(shape(feature["geometry"]), _WFS_SRID)
        county, municipality, settlement = _inads(tunnus) if tunnus else (None, None, None)
        return {
            "plot_id": tunnus,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "Maa-amet (Estonian Land Board)",
            "county": county,
            "municipality": municipality,
            "settlement": settlement,
        }
