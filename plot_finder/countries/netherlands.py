import re
from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import Point, shape

from plot_finder.exceptions import KadasterError, PlotNotFoundError
from plot_finder.utils import get, get_features, to_4326, transform_xy

_LOCSERVER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
_WFS_URL = "https://service.pdok.nl/kadaster/kadastralekaart/wfs/v5_0"
_RD_SRID = 28992

_POINT_RE = re.compile(r"POINT\(([-\d.]+)\s+([-\d.]+)\)")


def _locatieserver_lonlat(query: str) -> tuple[float, float]:
    resp = get(_LOCSERVER_URL, KadasterError, params={"q": query, "fq": "type:perceel", "rows": 1}, timeout=30)
    docs = resp.json().get("response", {}).get("docs", [])
    m = _POINT_RE.search(docs[0].get("centroide_ll", "")) if docs else None
    if not m:
        raise PlotNotFoundError(f"Parcel not found: {query}")
    return float(m.group(1)), float(m.group(2))


def _wfs_parcel_at(rd_x: float, rd_y: float) -> tuple:
    d = 30
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "kadastralekaartv5:Perceel",
        "outputFormat": "application/json",
        "srsName": f"EPSG:{_RD_SRID}",
        "bbox": f"{rd_x - d},{rd_y - d},{rd_x + d},{rd_y + d},urn:ogc:def:crs:EPSG::{_RD_SRID}",
        "count": 40,
    }
    point = Point(rd_x, rd_y)
    for feature in get_features(_WFS_URL, KadasterError, params=params):
        geom = shape(feature["geometry"])
        if geom.contains(point):
            return geom, feature["properties"]
    raise PlotNotFoundError(f"Parcel not found: xy={rd_x},{rd_y} (RD)")


class Netherlands(BaseModel):
    """Netherlands-specific parcel attributes, from the PDOK Kadaster."""

    municipality: str | None = None
    section: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "NL"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("municipality", "section", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            lon, lat = _locatieserver_lonlat(plot_id)
            rd_x, rd_y = transform_xy(lon, lat, 4326, _RD_SRID)
        else:
            rd_x, rd_y = transform_xy(x, y, srid, _RD_SRID)

        geom_rd, props = _wfs_parcel_at(rd_x, rd_y)
        geom = to_4326(geom_rd, _RD_SRID)

        gemeente = props.get("AKRKadastraleGemeenteCodeWaarde")
        sectie = props.get("sectie")
        number = props.get("perceelnummer")
        designation = " ".join(str(v) for v in (gemeente, sectie, number) if v is not None)
        return {
            "plot_id": designation or plot_id,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "PDOK Kadaster (Kadastrale Kaart)",
            "municipality": props.get("kadastraleGemeenteWaarde"),
            "section": sectie,
            "parcel_number": str(number) if number is not None else None,
        }
