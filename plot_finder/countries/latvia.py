from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import PlotNotFoundError, VZDError
from plot_finder.utils import get_features, transform_xy

_WFS_URL = (
    "https://geo-dpps.viss.gov.lv/api/DPPSPackage/client/"
    "Zemes_vien_423_0p2RBZ/5cc09e19-a238-4a2e-8eac-3a05cefa050e"
)
_TYPE = "cp:CadastralParcel"


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
    features = get_features(_WFS_URL, VZDError, params=params, timeout=60)
    return features[0] if features else None


class Latvia(BaseModel):
    """Latvia-specific parcel attributes, from Valsts zemes dienests (kadastrs.lv)."""

    territory_code: str | None = None
    group_code: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "LV"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("territory_code", "group_code", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"label='{plot_id}'")
        else:
            lon, lat = transform_xy(x, y, srid, 4326)
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
