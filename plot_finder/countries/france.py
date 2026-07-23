import json
from typing import ClassVar

import httpx
import shapely.geometry

from plot_finder.base import BasePlot
from plot_finder.exceptions import IGNError, PlotNotFoundError

_APICARTO_URL = "https://apicarto.ign.fr/api/cadastre/parcelle"


class FrancePlot(BasePlot):
    """A land parcel in France, from the IGN apicarto cadastre API.

    Coordinates are longitude (``x``) / latitude (``y``) in EPSG:4326.
    ``plot_id`` is the 14-character cadastral identifier (IDU),
    e.g. ``"33063000KE0078"``.
    """

    department: str | None = None      # code_dep, e.g. "33"
    insee: str | None = None           # commune INSEE code, e.g. "33063"
    commune: str | None = None         # commune name, e.g. "Bordeaux"
    section: str | None = None         # cadastral section, e.g. "KE"
    numero: str | None = None          # parcel number, e.g. "0078"

    srid: int = 4326
    _area_crs: ClassVar[int] = 2154

    def _fetch(self) -> None:
        if self.plot_id:
            pid = self.plot_id
            # IDU layout: code_insee(5) + com_abs(3) + section(2) + numero(4).
            # Note: for Paris/Lyon/Marseille the IDU carries the arrondissement
            # code rather than the base commune INSEE, so id lookup does not work
            # for those three cities — use coordinates or an address instead.
            if len(pid) != 14:
                raise IGNError(f"Invalid French cadastral id (expected 14 chars): {pid!r}")
            params = {
                "code_insee": pid[:5],
                "com_abs": pid[5:8],
                "section": pid[8:10],
                "numero": pid[10:14],
            }
        else:
            geom = {"type": "Point", "coordinates": [self.x, self.y]}
            params = {"geom": json.dumps(geom)}

        try:
            resp = httpx.get(_APICARTO_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise IGNError(f"IGN apicarto request failed: {exc}") from exc

        try:
            features = resp.json().get("features") or []
        except ValueError as exc:
            raise IGNError(f"Invalid JSON from IGN apicarto: {exc}") from exc

        if not features:
            query = f"xy={self.x},{self.y}" if self.x is not None else self.plot_id
            raise PlotNotFoundError(f"Parcel not found: {query}")

        props = features[0].get("properties", {})

        self.geom_wkt = shapely.geometry.shape(features[0]["geometry"]).wkt
        self.plot_id = props.get("idu") or self.plot_id
        self.department = props.get("code_dep")
        self.insee = props.get("code_insee") or props.get("code_com")
        self.commune = props.get("nom_com") or props.get("code_com")
        self.section = props.get("section")
        self.numero = props.get("numero")
        self.datasource = "IGN apicarto cadastre"
