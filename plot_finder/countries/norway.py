import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel

from plot_finder.exceptions import KartverketError, PlotNotFoundError
from plot_finder.utils import gml_attrs, gml_geometry, iter_features, to_4326, transform_xy

_WFS_URL = "https://wfs.geonorge.no/skwms1/wfs.matrikkelen-eiendomskart-teig"
_SRID = 25833
_NS = "http://skjema.geonorge.no/SOSI/produktspesifikasjon/Matrikkelen-Eiendomskart-Teig/20211101"

_ENVELOPE = (
    '<wfs:GetFeature service="WFS" version="2.0.0" count="1"'
    ' xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0"'
    ' xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:app="{ns}">'
    '<wfs:Query typeNames="app:Teig"><fes:Filter>{filter}</fes:Filter></wfs:Query></wfs:GetFeature>'
)


def _eq(field: str, value: str) -> str:
    ref = f"app:matrikkelenhet/app:Matrikkelenhet/app:{field}"
    return (
        f"<fes:PropertyIsEqualTo><fes:ValueReference>{ref}</fes:ValueReference>"
        f"<fes:Literal>{value}</fes:Literal></fes:PropertyIsEqualTo>"
    )


def _post(filter_xml: str):
    body = _ENVELOPE.format(ns=_NS, filter=filter_xml).encode("utf-8")
    try:
        resp = httpx.post(_WFS_URL, content=body, headers={"Content-Type": "application/xml"}, timeout=60)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise KartverketError(f"Kartverket WFS request failed: {exc}") from exc

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise KartverketError(f"Invalid GML from Kartverket: {exc}") from exc

    for feat in iter_features(root):
        geom = gml_geometry(feat, swap=False)
        if geom is not None:
            return gml_attrs(feat), geom
    return None


class Norway(BaseModel):
    """Norway-specific parcel attributes, from Kartverket (Matrikkelen)."""

    municipality: str | None = None
    municipality_code: str | None = None
    gnr: str | None = None
    bnr: str | None = None

    code: ClassVar[str] = "NO"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("municipality", "municipality_code", "gnr", "bnr")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            knr, _, rest = plot_id.partition("-")
            gnr, _, bnr = rest.partition("/")
            filter_xml = f"<fes:And>{_eq('kommunenummer', knr)}{_eq('gardsnummer', gnr)}{_eq('bruksnummer', bnr)}</fes:And>"
        else:
            east, north = transform_xy(x, y, srid, _SRID)
            filter_xml = (
                '<fes:Intersects><fes:ValueReference>app:område</fes:ValueReference>'
                f'<gml:Point srsName="urn:ogc:def:crs:EPSG::{_SRID}"><gml:pos>{east} {north}</gml:pos></gml:Point>'
                '</fes:Intersects>'
            )

        match = _post(filter_xml)
        if match is None:
            raise PlotNotFoundError(f"Parcel not found: {plot_id or f'xy={x},{y}'}")

        attrs, geom_st = match
        geom = to_4326(geom_st, _SRID)
        knr = attrs.get("kommunenummer")
        gnr = attrs.get("gardsnummer")
        bnr = attrs.get("bruksnummer")
        return {
            "plot_id": f"{knr}-{gnr}/{bnr}" if knr and gnr and bnr else plot_id,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "Kartverket (Matrikkelen)",
            "municipality": attrs.get("kommunenavn"),
            "municipality_code": knr,
            "gnr": gnr,
            "bnr": bnr,
        }
