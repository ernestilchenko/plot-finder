from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import PlotNotFoundError, RCError
from plot_finder.utils import get_features, transform_xy

_WFS_URL = "https://www.inspire-geoportal.lt/geoserver/cp/wfs"
_TYPE = "cp:CP.CadastralParcel"


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
    features = get_features(_WFS_URL, RCError, params=params, timeout=60)
    return features[0] if features else None


class Lithuania(BaseModel):
    """Lithuania-specific parcel attributes, from Registrų centras (geoportal.lt)."""

    cadastral_zone: str | None = None
    municipality_code: str | None = None
    purpose: str | None = None

    code: ClassVar[str] = "LT"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("cadastral_zone", "municipality_code", "purpose")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"label='{plot_id}'")
        else:
            lon, lat = transform_xy(x, y, srid, 4326)
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
