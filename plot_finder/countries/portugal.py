from typing import ClassVar

import httpx
from pydantic import BaseModel
from shapely.geometry import Point, shape

from plot_finder.exceptions import DGTError, PlotNotFoundError
from plot_finder.utils import get_features, to_4326, transform_xy

_WFS_URL = "https://snic.dgterritorio.gov.pt/geoserver/snic/ows"
_REST_URL = "https://snic.dgterritorio.gov.pt/geoportal/dgt_snic2/api/app/search/predio/nic"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://snic.dgterritorio.gov.pt/visualizadorCadastro",
}
_WFS_SRID = 3857


def _wfs(extra: dict) -> list:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "snic:x_predios",
        "outputFormat": "application/json",
        "srsName": f"EPSG:{_WFS_SRID}",
        **extra,
    }
    return get_features(_WFS_URL, DGTError, params=params, headers=_HEADERS)


def _rest_attrs(nic: str) -> tuple[str | None, str | None, str | None]:
    try:
        resp = httpx.get(_REST_URL, params={"filter": nic}, headers=_HEADERS, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            data = data[0] if data else {}
        return data.get("concelho"), data.get("des_simpli"), data.get("dico")
    except (httpx.HTTPError, ValueError, IndexError):
        return (None, None, None)


class Portugal(BaseModel):
    """Portugal-specific parcel attributes, from the DGT SNIC (partial coverage)."""

    municipality: str | None = None
    parish: str | None = None
    district_code: str | None = None

    code: ClassVar[str] = "PT"
    default_srid: ClassVar[int] = 4326
    attributes: ClassVar[tuple[str, ...]] = ("municipality", "parish", "district_code")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            features = _wfs({"cql_filter": f"nic='{plot_id}'", "count": 1})
            feature = features[0] if features else None
        else:
            px, py = transform_xy(x, y, srid, _WFS_SRID)
            d = 5
            features = _wfs({"bbox": f"{px - d},{py - d},{px + d},{py + d},EPSG:{_WFS_SRID}", "count": 30})
            point = Point(px, py)
            feature = next((f for f in features if shape(f["geometry"]).contains(point)), None)

        if feature is None:
            raise PlotNotFoundError(
                f"Parcel not found: {plot_id or f'xy={x},{y}'} "
                "(Portugal SNIC coverage is partial — cities and the north are not cadastred)"
            )

        props = feature["properties"]
        nic = props.get("nic")
        geom = to_4326(shape(feature["geometry"]), _WFS_SRID)
        municipality, parish, district_code = _rest_attrs(nic) if nic else (None, None, None)
        return {
            "plot_id": nic,
            "geom_wkt": geom.wkt,
            "geom_extent": None,
            "datasource": "DGT SNIC (Sistema Nacional de Informação Cadastral)",
            "municipality": municipality,
            "parish": parish,
            "district_code": district_code,
        }
