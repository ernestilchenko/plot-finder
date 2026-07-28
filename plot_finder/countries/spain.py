import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel

from plot_finder.exceptions import CatastroError, PlotNotFoundError
from plot_finder.utils import gml_geometry

_RCCOOR_URL = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR"
_DNPRC_URL = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"
_WFS_URL = "http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"

_CAT = "{http://www.catastro.meh.es/}"
_GML = "{http://www.opengis.net/gml/3.2}"
_CP = "{http://inspire.ec.europa.eu/schemas/cp/4.0}"


def _rccoor(x: float, y: float, srid: int) -> str:
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
    geom = gml_geometry(parcel, swap=True) if parcel is not None else None
    if geom is None:
        raise PlotNotFoundError(f"Parcel not found: {refcat}")
    ref = parcel.get(_GML + "id", "").replace("ES.SDGC.CP.", "") or ref14
    return geom.wkt, ref


class Spain(BaseModel):
    """Spain-specific parcel attributes, from the Dirección General del Catastro."""

    province: str | None = None
    municipality: str | None = None

    code: ClassVar[str] = "ES"
    default_srid: ClassVar[int] = 4326
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
