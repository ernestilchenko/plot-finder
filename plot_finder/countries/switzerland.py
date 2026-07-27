from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import Point, shape

from plot_finder.countries._geo import to_4326
from plot_finder.exceptions import GeoAdminError, PlotNotFoundError

_BASE = "https://api3.geo.admin.ch/rest/services/all/MapServer"
_PARCEL_LAYER = "ch.kantone.cadastralwebmap-farbe"
_GEMEINDE_LAYER = "ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill"


def _props(feature: dict) -> dict:
    return feature.get("attributes") or feature.get("properties") or {}


def _identify(x: float, y: float, srid: int, layer: str, geometry: bool) -> list:
    d = 0.001 if srid == 4326 else 60
    params = {
        "geometry": f"{x},{y}",
        "geometryType": "esriGeometryPoint",
        "imageDisplay": "100,100,96",
        "mapExtent": f"{x - d},{y - d},{x + d},{y + d}",
        "tolerance": "0",
        "layers": f"all:{layer}",
        "returnGeometry": "true" if geometry else "false",
        "geometryFormat": "geojson",
        "sr": str(srid),
    }
    try:
        resp = httpx.get(f"{_BASE}/identify", params=params, timeout=40)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise GeoAdminError(f"geo.admin.ch identify failed: {exc}") from exc
    return resp.json().get("results", [])


def _find_egrid(egrid: str, srid: int) -> dict:
    params = {
        "layer": _PARCEL_LAYER,
        "searchField": "egris_egrid",
        "searchText": egrid,
        "returnGeometry": "true",
        "geometryFormat": "geojson",
        "sr": str(srid),
    }
    try:
        resp = httpx.get(f"{_BASE}/find", params=params, timeout=40)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise GeoAdminError(f"geo.admin.ch find failed: {exc}") from exc
    results = resp.json().get("results", [])
    if not results:
        raise PlotNotFoundError(f"Parcel not found: {egrid}")
    return results[0]


def _municipality(x: float, y: float, srid: int) -> tuple[str | None, str | None]:
    try:
        results = _identify(x, y, srid, _GEMEINDE_LAYER, geometry=False)
    except GeoAdminError:
        return (None, None)
    current = [r for r in results if _props(r).get("is_current_jahr") in (True, "true")]
    props = _props((current or results)[0]) if (current or results) else {}
    return props.get("gemname"), props.get("kanton")


class Switzerland(BaseModel):
    """Switzerland-specific parcel attributes, from swisstopo (geo.admin.ch)."""

    canton: str | None = None
    municipality: str | None = None
    egrid: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "CH"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 2056
    attributes: ClassVar[tuple[str, ...]] = ("canton", "municipality", "egrid", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _find_egrid(plot_id, srid)
        else:
            results = _identify(x, y, srid, _PARCEL_LAYER, geometry=True)
            if not results:
                raise PlotNotFoundError(f"Parcel not found: xy={x},{y}")
            point = Point(x, y)
            feature = next((r for r in results if shape(r["geometry"]).contains(point)), results[0])

        geom = to_4326(shape(feature["geometry"]), srid)
        props = _props(feature)
        municipality, kanton = _municipality(geom.centroid.x, geom.centroid.y, 4326)
        return {
            "plot_id": props.get("egris_egrid") or plot_id,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "swisstopo (geo.admin.ch)",
            "canton": props.get("ak") or kanton,
            "municipality": municipality,
            "egrid": props.get("egris_egrid"),
            "parcel_number": props.get("number"),
        }
