import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import Point, shape

from plot_finder.exceptions import ALKISError, PlotNotFoundError
from plot_finder.utils import get, get_features, gml_attrs, gml_geometry, iter_features, to_4326, transform_xy

_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
_HEADERS = {"User-Agent": "plot-finder/1.0"}

# ISO 3166-2 code -> (WFS url, typeName, UTM srid, family, land code, land name)
_STATES = {
    "DE-NW": ("https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-flurstuecke_alkis", "cp:CadastralParcel", 25832, "cp", "05", "Nordrhein-Westfalen"),
    "DE-BB": ("https://inspire.brandenburg.de/services/cp_alkis_wfs", "cp:CadastralParcel", 25833, "cp", "12", "Brandenburg"),
    "DE-NI": ("https://www.inspire.niedersachsen.de/doorman/noauth/alkis-dls-cp", "cp:CadastralParcel", 25832, "cp", "03", "Niedersachsen"),
    "DE-MV": ("https://www.geodaten-mv.de/dienste/inspire_cp_alkis_download", "cp:CadastralParcel", 25833, "cp", "13", "Mecklenburg-Vorpommern"),
    "DE-ST": ("https://www.geodatenportal.sachsen-anhalt.de/ows_INSPIRE_LVermGeo_ALKIS_CP_WFS", "cp:CadastralParcel", 25832, "cp", "15", "Sachsen-Anhalt"),
    "DE-SN": ("https://geodienste.sachsen.de/aaa/public_inspire/alkis/cp/dls/wfs", "cp:CadastralParcel", 25832, "cp", "14", "Sachsen"),
    "DE-HH": ("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Flurstuecke", "cp:CadastralParcel", 25832, "cp", "02", "Hamburg"),
    "DE-TH": ("https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs", "ave:Flurstueck", 25832, "ave", "16", "Thüringen"),
    "DE-HB": ("https://geodienste.bremen.de/wfs_hduk2958loah3976niun", "app:flurstuecke", 25832, "ave", "04", "Bremen"),
    "DE-BE": ("https://gdi.berlin.de/services/wfs/alkis_flurstuecke", "alkis_flurstuecke:flurstuecke", 25833, "berlin", "11", "Berlin"),
}


def _reverse_state(lon: float, lat: float) -> str | None:
    try:
        resp = httpx.get(
            _REVERSE_URL,
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("address", {}).get("ISO3166-2-lvl4")
    except (httpx.HTTPError, ValueError):
        return None


def _query(url: str, typename: str, srid: int, family: str, east: float, north: float) -> list:
    d = 6
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": typename,
        "SRSNAME": f"urn:ogc:def:crs:EPSG::{srid}",
        "BBOX": f"{east - d},{north - d},{east + d},{north + d},urn:ogc:def:crs:EPSG::{srid}",
        "COUNT": 20,
    }
    if family == "berlin":
        params["OUTPUTFORMAT"] = "application/json"
        feats = get_features(url, ALKISError, params=params, headers=_HEADERS, timeout=60)
        return [(f.get("properties", {}), shape(f["geometry"])) for f in feats]

    resp = get(url, ALKISError, params=params, headers=_HEADERS, timeout=60)
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise ALKISError(f"Invalid GML from ALKIS WFS: {exc}") from exc
    out = []
    for feat in iter_features(root):
        geom = gml_geometry(feat, swap=False)
        if geom is not None:
            out.append((gml_attrs(feat), geom))
    return out


def _parse_fsk(ncr: str) -> dict:
    return {
        "gemarkung": ncr[2:6] or None,
        "flur": ncr[6:9] or None,
        "zaehler": ncr[9:14].lstrip("0") or "0",
        "nenner": ncr[14:18].replace("_", "").lstrip("0") or None,
    }


def _zn(zae: str | None, nen: str | None) -> str | None:
    if not zae:
        return None
    return f"{zae}/{nen}" if nen else str(zae)


class Germany(BaseModel):
    """Germany-specific parcel attributes, from the state ALKIS / INSPIRE services."""

    land: str | None = None
    gemarkung: str | None = None
    flur: str | None = None
    parcel_number: str | None = None

    code: ClassVar[str] = "DE"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("land", "gemarkung", "flur", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if x is None:
            raise ALKISError(
                "Germany supports lookup by coordinates or address only — the state "
                "ALKIS services vary too much for a uniform id lookup."
            )

        lon, lat = transform_xy(x, y, srid, 4326)
        iso = _reverse_state(lon, lat)
        if iso not in _STATES:
            raise ALKISError(
                f"No free cadastral service for {iso or 'this location'}. "
                f"Supported states: {', '.join(sorted(_STATES))}"
            )
        url, typename, st_srid, family, land_code, land_name = _STATES[iso]

        east, north = transform_xy(lon, lat, 4326, st_srid)
        point = Point(east, north)
        match = next((f for f in _query(url, typename, st_srid, family, east, north) if f[1].contains(point)), None)
        if match is None:
            raise PlotNotFoundError(f"Parcel not found: xy={lon},{lat} ({land_name})")

        attrs, geom_st = match
        geom = to_4326(geom_st, st_srid)

        if family == "cp":
            ncr = attrs.get("nationalCadastralReference") or ""
            parsed = _parse_fsk(ncr)
            key = ncr or None
            gemarkung, flur = parsed["gemarkung"], parsed["flur"]
            parcel = attrs.get("label") or _zn(parsed["zaehler"], parsed["nenner"])
        elif family == "berlin":
            key = attrs.get("fsko")
            gemarkung = attrs.get("namgmk") or attrs.get("gmk")
            flur = attrs.get("fln")
            parcel = _zn(attrs.get("zae"), attrs.get("nen"))
        else:
            key = attrs.get("flstkennz")
            gemarkung = attrs.get("gemarkung")
            flur = attrs.get("flur")
            parcel = _zn(attrs.get("flstnrzae"), attrs.get("flstnrnen")) or attrs.get("flurstnr")

        return {
            "plot_id": key,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": f"ALKIS {land_name}",
            "land": land_code,
            "gemarkung": gemarkung,
            "flur": flur,
            "parcel_number": parcel,
        }
