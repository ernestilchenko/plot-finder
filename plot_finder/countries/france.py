import json
from typing import ClassVar

import httpx
import shapely.geometry
from pydantic import BaseModel

from plot_finder.exceptions import IGNError, PlotNotFoundError

_APICARTO_URL = "https://apicarto.ign.fr/api/cadastre/parcelle"


class France(BaseModel):
    """France-specific parcel attributes, from the IGN apicarto cadastre API."""

    department: str | None = None
    insee: str | None = None
    commune: str | None = None
    section: str | None = None
    numero: str | None = None

    code: ClassVar[str] = "FR"
    default_srid: ClassVar[int] = 4326
    area_crs: ClassVar[int] = 2154
    attributes: ClassVar[tuple[str, ...]] = ("department", "insee", "commune", "section", "numero")

    @staticmethod
    def fetch(plot_id: str | None, x: float | None, y: float | None, srid: int) -> dict:
        if plot_id:
            if len(plot_id) != 14:
                raise IGNError(f"Invalid French cadastral id (expected 14 chars): {plot_id!r}")
            params = {
                "code_insee": plot_id[:5],
                "com_abs": plot_id[5:8],
                "section": plot_id[8:10],
                "numero": plot_id[10:14],
            }
        else:
            params = {"geom": json.dumps({"type": "Point", "coordinates": [x, y]})}

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
            query = f"xy={x},{y}" if x is not None else plot_id
            raise PlotNotFoundError(f"Parcel not found: {query}")

        props = features[0].get("properties", {})
        return {
            "plot_id": props.get("idu") or plot_id,
            "geom_wkt": shapely.geometry.shape(features[0]["geometry"]).wkt,
            "geom_extent": None,
            "datasource": "IGN apicarto cadastre",
            "department": props.get("code_dep"),
            "insee": props.get("code_insee") or props.get("code_com"),
            "commune": props.get("nom_com") or props.get("code_com"),
            "section": props.get("section"),
            "numero": props.get("numero"),
        }
