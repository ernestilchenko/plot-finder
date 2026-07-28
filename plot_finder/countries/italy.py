import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import MultiPolygon, Point, Polygon

from plot_finder.exceptions import AdEError, PlotNotFoundError

_WFS_URL = "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php"
_SRS = "urn:ogc:def:crs:EPSG::6706"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}
_ATTR_TAGS = ("NATIONALCADASTRALREFERENCE", "ADMINISTRATIVEUNIT", "LABEL")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rings(parcel: ET.Element, kind: str) -> list[list[tuple[float, float]]]:
    rings = []
    for holder in parcel.iter():
        if _local(holder.tag) != kind:
            continue
        poslist = next((e for e in holder.iter() if _local(e.tag) == "posList"), None)
        if poslist is not None and poslist.text:
            nums = [float(v) for v in poslist.text.split()]
            rings.append([(nums[i + 1], nums[i]) for i in range(0, len(nums), 2)])
    return rings


def _geometry(parcel: ET.Element):
    shells = _rings(parcel, "exterior")
    if not shells:
        return None
    if len(shells) == 1:
        return Polygon(shells[0], _rings(parcel, "interior"))
    return MultiPolygon([Polygon(s) for s in shells])


def _wfs(extra: dict) -> list[tuple[dict, object]]:
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": "CP:CadastralParcel",
        "SRSNAME": _SRS,
        **extra,
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, headers=_HEADERS, timeout=90, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AdEError(f"Agenzia delle Entrate WFS request failed: {exc}") from exc

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise AdEError(f"Invalid GML from Agenzia delle Entrate: {exc}") from exc

    parcels = []
    for el in root.iter():
        if _local(el.tag) != "CadastralParcel":
            continue
        attrs = {_local(c.tag): c.text.strip() for c in el.iter() if _local(c.tag) in _ATTR_TAGS and c.text}
        geom = _geometry(el)
        if geom is not None:
            parcels.append((attrs, geom))
    return parcels


def _to_4326_lonlat(x: float, y: float, srid: int) -> tuple[float, float]:
    if srid == 4326:
        return x, y
    from pyproj import Transformer
    return Transformer.from_crs(f"EPSG:{srid}", "EPSG:4326", always_xy=True).transform(x, y)


class Italy(BaseModel):
    """Italy-specific parcel attributes, from Agenzia delle Entrate (INSPIRE)."""

    comune_code: str | None = None
    foglio: str | None = None
    particella: str | None = None

    code: ClassVar[str] = "IT"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 25832
    attributes: ClassVar[tuple[str, ...]] = ("comune_code", "foglio", "particella")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if x is None:
            raise AdEError(
                "Italy supports lookup by coordinates or address only — the Agenzia "
                "delle Entrate WFS does not allow filtering by cadastral reference."
            )

        lon, lat = _to_4326_lonlat(x, y, srid)
        d = 0.0004
        parcels = _wfs({"BBOX": f"{lat - d},{lon - d},{lat + d},{lon + d},{_SRS}", "COUNT": 15})
        point = Point(lon, lat)
        match = next(
            (
                (attrs, geom)
                for attrs, geom in parcels
                if not (attrs.get("LABEL") or "").startswith(("STRADA", "ACQUA"))
                and geom.contains(point)
            ),
            None,
        )

        if match is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        attrs, geom = match
        ref = attrs.get("NATIONALCADASTRALREFERENCE") or plot_id
        return {
            "plot_id": ref,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "Agenzia delle Entrate (INSPIRE)",
            "comune_code": attrs.get("ADMINISTRATIVEUNIT"),
            "foglio": ref[5:9] if ref and len(ref) >= 9 else None,
            "particella": attrs.get("LABEL"),
        }
