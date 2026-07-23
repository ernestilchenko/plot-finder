import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import MultiPolygon, Polygon

from plot_finder.exceptions import CatastroError, PlotNotFoundError

_RCCOOR_URL = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR"
_DNPRC_URL = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"
_WFS_URL = "http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"

_CAT = "{http://www.catastro.meh.es/}"
_GML = "{http://www.opengis.net/gml/3.2}"
_CP = "{http://inspire.ec.europa.eu/schemas/cp/4.0}"


def _ring(elem: ET.Element) -> list[tuple[float, float]]:
    """Read a GML LinearRing posList as (lon, lat) pairs (GML EPSG:4326 is lat/lon)."""
    nums = [float(v) for v in next(elem.iter(_GML + "posList")).text.split()]
    return [(nums[i + 1], nums[i]) for i in range(0, len(nums), 2)]


def _parse_geometry(parcel: ET.Element):
    polys = []
    for patch in parcel.iter(_GML + "PolygonPatch"):
        shell = _ring(patch.find(_GML + "exterior"))
        holes = [_ring(i) for i in patch.findall(_GML + "interior")]
        polys.append(Polygon(shell, holes))
    if not polys:
        raise CatastroError("No geometry in Catastro WFS response")
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def _rccoor(x: float, y: float, srid: int) -> str:
    """Resolve coordinates to a cadastral reference (referencia catastral)."""
    params = {"SRS": f"EPSG:{srid}", "Coordenada_X": str(x), "Coordenada_Y": str(y)}
    try:
        resp = httpx.get(_RCCOOR_URL, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise CatastroError(f"Catastro RCCOOR request failed: {exc}") from exc

    root = ET.fromstring(resp.content)
    pc1 = root.find(f".//{_CAT}pc1")
    pc2 = root.find(f".//{_CAT}pc2")
    if pc1 is None or pc2 is None or not pc1.text:
        raise PlotNotFoundError(f"Parcel not found: xy={x},{y}")
    return pc1.text + pc2.text


def _dnprc(refcat: str) -> tuple[str | None, str | None]:
    """Best-effort province / municipality lookup for a cadastral reference."""
    try:
        resp = httpx.get(_DNPRC_URL, params={"Provincia": "", "Municipio": "", "RC": refcat}, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        np = root.find(f".//{_CAT}np")
        nm = root.find(f".//{_CAT}nm")
        return (np.text if np is not None else None, nm.text if nm is not None else None)
    except (httpx.HTTPError, ET.ParseError):
        return (None, None)


def _wfs_geometry(refcat: str) -> tuple[str, str]:
    """Fetch parcel geometry (as WKT) and the canonical reference from the INSPIRE WFS."""
    ref14 = refcat[:14]
    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "GetFeature",
        "STOREDQUERIE_ID": "GetParcel",
        "refcat": ref14,
        "srsname": "EPSG::4326",
    }
    try:
        resp = httpx.get(_WFS_URL, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise CatastroError(f"Catastro WFS request failed: {exc}") from exc

    parcel = next(ET.fromstring(resp.content).iter(_CP + "CadastralParcel"), None)
    if parcel is None:
        raise PlotNotFoundError(f"Parcel not found: {refcat}")

    ref = parcel.get(_GML + "id", "").replace("ES.SDGC.CP.", "") or ref14
    return _parse_geometry(parcel).wkt, ref


class Spain(BaseModel):
    """Spain-specific parcel attributes, from the Dirección General del Catastro."""

    province: str | None = None      # provincia, e.g. "MADRID"
    municipality: str | None = None  # municipio, e.g. "MADRID"

    code: ClassVar[str] = "ES"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 25830  # ETRS89 / UTM zone 30N
    attributes: ClassVar[tuple[str, ...]] = ("province", "municipality")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        refcat = plot_id or _rccoor(x, y, srid)
        geom_wkt, ref = _wfs_geometry(refcat)
        province, municipality = _dnprc(ref)
        return {
            "plot_id": ref,
            "geom_wkt": geom_wkt,
            "geom_extent": None,
            "datasource": "Dirección General del Catastro",
            "province": province,
            "municipality": municipality,
        }
