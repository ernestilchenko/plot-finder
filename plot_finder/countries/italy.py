import xml.etree.ElementTree as ET
from typing import ClassVar

from pydantic import BaseModel
from shapely.geometry import Point

from plot_finder.exceptions import AdEError, PlotNotFoundError
from plot_finder.utils import get, gml_attrs, gml_geometry, iter_features, transform_xy

_WFS_URL = "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/owfs01.php"
_SRS = "urn:ogc:def:crs:EPSG::6706"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}


def _wfs(extra: dict) -> list[tuple[dict, object]]:
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": "CP:CadastralParcel",
        "SRSNAME": _SRS,
        **extra,
    }
    resp = get(_WFS_URL, AdEError, params=params, headers=_HEADERS, timeout=90)
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise AdEError(f"Invalid GML from Agenzia delle Entrate: {exc}") from exc

    parcels = []
    for feat in iter_features(root, "CadastralParcel"):
        geom = gml_geometry(feat, swap=True)
        if geom is not None:
            parcels.append((gml_attrs(feat), geom))
    return parcels


class Italy(BaseModel):
    """Italy-specific parcel attributes, from Agenzia delle Entrate (INSPIRE)."""

    comune_code: str | None = None
    foglio: str | None = None
    particella: str | None = None

    code: ClassVar[str] = "IT"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("comune_code", "foglio", "particella")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if x is None:
            raise AdEError(
                "Italy supports lookup by coordinates or address only — the Agenzia "
                "delle Entrate WFS does not allow filtering by cadastral reference."
            )

        lon, lat = transform_xy(x, y, srid, 4326)
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
