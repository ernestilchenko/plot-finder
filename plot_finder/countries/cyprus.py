import json
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import DLSError, PlotNotFoundError

_QUERY_URL = (
    "https://eservices.dls.moi.gov.cy/inspire/rest/services/INSPIRE/"
    "CP_CadastralParcels/MapServer/1/query"
)


def _query(extra: dict) -> dict | None:
    params = {"outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson", **extra}
    try:
        resp = httpx.get(_QUERY_URL, params=params, timeout=40, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise DLSError(f"Cyprus DLS request failed: {exc}") from exc
    try:
        features = resp.json().get("features") or []
    except ValueError as exc:
        raise DLSError(f"Invalid JSON from Cyprus DLS: {exc}") from exc
    return features[0] if features else None


def _drop_z(geom):
    if geom.has_z:
        from shapely.ops import transform
        return transform(lambda *c: c[:2], geom)
    return geom


class Cyprus(BaseModel):
    """Cyprus-specific parcel attributes, from the Department of Lands and Surveys."""

    district_code: str | None = None
    sheet: str | None = None
    plan: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "CY"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 32636
    attributes: ClassVar[tuple[str, ...]] = ("district_code", "sheet", "plan", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _query({"where": f"nationalCadastralRef='{plot_id}'"})
        else:
            geometry = json.dumps({"x": x, "y": y, "spatialReference": {"wkid": srid}})
            feature = _query({
                "geometry": geometry,
                "geometryType": "esriGeometryPoint",
                "inSR": str(srid),
                "spatialRel": "esriSpatialRelIntersects",
            })

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature.get("properties", {})
        ref = props.get("nationalCadastralRef") or plot_id or ""
        parts = ref.split("-")
        district_code = parts[0] if parts and parts[0] else None
        sheet = plan = None
        if len(parts) >= 2 and "/" in parts[1]:
            sheet, plan = parts[1].split("/", 1)
        label = props.get("label")

        return {
            "plot_id": ref or None,
            "geom_wkt": _drop_z(shape(feature["geometry"])).wkt,
            "geom_extent": None,
            "datasource": "Cyprus DLS (INSPIRE)",
            "district_code": district_code,
            "sheet": sheet,
            "plan": plan,
            "parcel_number": str(label) if label is not None else (parts[-1] if parts else None),
        }
