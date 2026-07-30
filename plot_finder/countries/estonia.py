from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import shape

from plot_finder.exceptions import MaaametError, PlotNotFoundError
from plot_finder.utils import get_features, to_4326, transform_xy

_WFS_URL = "https://gsavalik.envir.ee/geoserver/wfs"
_TYPE = "kataster:ky_kehtiv"
_WFS_SRID = 3301


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
    features = get_features(_WFS_URL, MaaametError, params=params)
    return features[0] if features else None


class Estonia(BaseModel):
    """Estonia-specific parcel attributes, from the Maa-amet (kataster)."""

    county: str | None = None
    municipality: str | None = None
    settlement: str | None = None

    code: ClassVar[str] = "EE"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("county", "municipality", "settlement")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            feature = _wfs(f"tunnus='{plot_id}'")
        else:
            east, north = transform_xy(x, y, srid, _WFS_SRID)
            feature = _wfs(f"INTERSECTS(geom, POINT({north} {east}))")

        if feature is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        props = feature["properties"]
        geom = to_4326(shape(feature["geometry"]), _WFS_SRID)
        return {
            "plot_id": props.get("tunnus"),
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "Maa-amet (kataster)",
            "county": props.get("mk_nimi"),
            "municipality": props.get("ov_nimi"),
            "settlement": props.get("ay_nimi"),
        }
