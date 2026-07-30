from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import CadGISError, PlotNotFoundError
from plot_finder.utils import get_features

_QUERY_URL = (
    "https://ccff02.minfin.fgov.be/geoservices/arcgis/rest/services/"
    "INSPIRE/CP/MapServer/1/query"
)


def _query(extra: dict) -> dict | None:
    params = {"outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geoJSON", **extra}
    features = get_features(_QUERY_URL, CadGISError, params=params, timeout=60)
    return features[0] if features else None


class Belgium(BaseModel):
    """Belgium-specific parcel attributes, from FPS Finance CadGIS (INSPIRE)."""

    nis_code: str | None = None
    section: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "BE"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("nis_code", "section", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _query({"where": f"nationalCadastralRef='{plot_id}'"})
        else:
            feature = _query({
                "geometry": f"{x},{y}",
                "geometryType": "esriGeometryPoint",
                "inSR": str(srid),
                "spatialRel": "esriSpatialRelIntersects",
            })

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature["properties"]
        capakey = props.get("nationalCadastralRef") or plot_id or ""
        geom = shape(feature["geometry"])
        return {
            "plot_id": capakey or None,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "FPS Finance CadGIS (INSPIRE)",
            "nis_code": capakey[:5] if len(capakey) >= 5 else None,
            "section": capakey[5] if len(capakey) >= 6 else None,
            "parcel_number": props.get("label"),
        }
