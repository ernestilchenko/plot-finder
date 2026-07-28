import json
from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import DLSError, PlotNotFoundError
from plot_finder.utils import drop_z, get_features

_QUERY_URL = (
    "https://eservices.dls.moi.gov.cy/inspire/rest/services/INSPIRE/"
    "CP_CadastralParcels/MapServer/1/query"
)


def _query(extra: dict) -> dict | None:
    params = {"outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson", **extra}
    features = get_features(_QUERY_URL, DLSError, params=params)
    return features[0] if features else None


class Cyprus(BaseModel):
    """Cyprus-specific parcel attributes, from the Department of Lands and Surveys."""

    district_code: str | None = None
    sheet: str | None = None
    plan: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "CY"
    default_srid: ClassVar[int] = 4326
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
            "geom_wkt": drop_z(shape(feature["geometry"])).wkt,
            "geom_extent": None,
            "datasource": "Cyprus DLS (INSPIRE)",
            "district_code": district_code,
            "sheet": sheet,
            "plan": plan,
            "parcel_number": str(label) if label is not None else (parts[-1] if parts else None),
        }
