
import re
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import Point, shape

from plot_finder.exceptions import KadasterError, PlotNotFoundError

_LOCSERVER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
_WFS_URL = "https://service.pdok.nl/kadaster/kadastralekaart/wfs/v5_0"

_POINT_RE = re.compile(r"POINT\(([-\d.]+)\s+([-\d.]+)\)")


def _to_rd():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)


def _to_wgs():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def _locatieserver_lonlat(query: str) -> tuple[float, float]:
    params = {"q": query, "fq": "type:perceel", "rows": 1}
    try:
        resp = httpx.get(_LOCSERVER_URL, params=params, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise KadasterError(f"PDOK Locatieserver request failed: {exc}") from exc

    docs = resp.json().get("response", {}).get("docs", [])
    if not docs:
        raise PlotNotFoundError(f"Parcel not found: {query}")
    m = _POINT_RE.search(docs[0].get("centroide_ll", ""))
    if not m:
        raise PlotNotFoundError(f"Parcel not found: {query}")
    return float(m.group(1)), float(m.group(2))


def _wfs_parcel_at(rd_x: float, rd_y: float) -> tuple:
    d = 30
    bbox = f"{rd_x - d},{rd_y - d},{rd_x + d},{rd_y + d},urn:ogc:def:crs:EPSG::28992"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "kadastralekaartv5:Perceel",
        "outputFormat": "application/json",
        "srsName": "EPSG:28992",
        "bbox": bbox,
        "count": 40,
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, timeout=40, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise KadasterError(f"PDOK WFS request failed: {exc}") from exc

    point = Point(rd_x, rd_y)
    for feature in resp.json().get("features", []):
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
    area_crs: ClassVar[int] = 28992
    attributes: ClassVar[tuple[str, ...]] = ("municipality", "section", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            lon, lat = _locatieserver_lonlat(plot_id)
            rd_x, rd_y = _to_rd().transform(lon, lat)
        elif srid == 28992:
            rd_x, rd_y = x, y
        else:
            rd_x, rd_y = _to_rd().transform(x, y)

        geom_rd, props = _wfs_parcel_at(rd_x, rd_y)
        from shapely.ops import transform as shp_transform
        geom_wgs = shp_transform(_to_wgs().transform, geom_rd)

        gemeente = props.get("AKRKadastraleGemeenteCodeWaarde")
        sectie = props.get("sectie")
        number = props.get("perceelnummer")
        designation = " ".join(str(v) for v in (gemeente, sectie, number) if v is not None)
        return {
            "plot_id": designation or plot_id,
            "geom_wkt": geom_wgs.wkt,
            "geom_extent": None,
            "datasource": "PDOK Kadaster (Kadastrale Kaart)",
            "municipality": props.get("kadastraleGemeenteWaarde"),
            "section": sectie,
            "parcel_number": str(number) if number is not None else None,
        }
