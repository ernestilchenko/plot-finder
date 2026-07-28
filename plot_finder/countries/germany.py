import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import MultiPolygon, Point, Polygon, shape

from plot_finder.countries._geo import to_4326
from plot_finder.exceptions import ALKISError, PlotNotFoundError

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


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rings(feat: ET.Element, kind: str) -> list[list[tuple[float, float]]]:
    rings = []
    for holder in feat.iter():
        if _local(holder.tag) != kind:
            continue
        coords: list[tuple[float, float]] = []
        for node in holder.iter():
            if _local(node.tag) in ("posList", "pos") and node.text:
                nums = [float(v) for v in node.text.split()]
                coords += [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]
        if len(coords) >= 4:
            rings.append(coords)
    return rings


def _geometry(feat: ET.Element):
    shells = _rings(feat, "exterior")
    if not shells:
        return None
    holes = _rings(feat, "interior")
    if len(shells) == 1:
        return Polygon(shells[0], holes)
    return MultiPolygon([Polygon(s) for s in shells])


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
    bbox = f"{east - d},{north - d},{east + d},{north + d},urn:ogc:def:crs:EPSG::{srid}"
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": typename,
        "SRSNAME": f"urn:ogc:def:crs:EPSG::{srid}",
        "BBOX": bbox,
        "COUNT": 20,
    }
    if family == "berlin":
        params["OUTPUTFORMAT"] = "application/json"
    try:
        resp = httpx.get(url, params=params, headers=_HEADERS, timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ALKISError(f"ALKIS WFS request failed: {exc}") from exc

    if family == "berlin":
        try:
            feats = resp.json().get("features") or []
        except ValueError as exc:
            raise ALKISError(f"Invalid JSON from Berlin ALKIS: {exc}") from exc
        return [(f.get("properties", {}), shape(f["geometry"])) for f in feats]

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise ALKISError(f"Invalid GML from ALKIS WFS: {exc}") from exc
    out = []
    for member in root.iter():
        if _local(member.tag) not in ("member", "featureMember"):
            continue
        feat = next(iter(member), None)
        if feat is None:
            continue
        geom = _geometry(feat)
        if geom is None:
            continue
        attrs = {_local(e.tag): e.text.strip() for e in feat.iter() if not list(e) and e.text and e.text.strip()}
        out.append((attrs, geom))
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
    area_crs: ClassVar[int] = 3035
    attributes: ClassVar[tuple[str, ...]] = ("land", "gemarkung", "flur", "parcel_number")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if x is None:
            raise ALKISError(
                "Germany supports lookup by coordinates or address only — the state "
                "ALKIS services vary too much for a uniform id lookup."
            )

        if srid == 4326:
            lon, lat = x, y
        else:
            from pyproj import Transformer
            lon, lat = Transformer.from_crs(f"EPSG:{srid}", "EPSG:4326", always_xy=True).transform(x, y)

        iso = _reverse_state(lon, lat)
        if iso not in _STATES:
            raise ALKISError(
                f"No free cadastral service for {iso or 'this location'}. "
                f"Supported states: {', '.join(sorted(_STATES))}"
            )
        url, typename, st_srid, family, land_code, land_name = _STATES[iso]

        from pyproj import Transformer
        east, north = Transformer.from_crs("EPSG:4326", f"EPSG:{st_srid}", always_xy=True).transform(lon, lat)
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
