from __future__ import annotations

from pydantic import BaseModel


class PlanZone(BaseModel):
    """Single planning zone (strefa planistyczna) from POG."""

    designation: str | None = None
    symbol: str | None = None
    symbol_name: str | None = None
    valid_from: str | None = None
    max_building_intensity: float | None = None
    max_building_coverage_pct: float | None = None
    max_building_height_m: float | None = None
    min_bio_active_pct: float | None = None


class POG(BaseModel):
    """Plan Ogolny Gminy (General Municipal Plan)."""

    has_plan: bool = False
    plan_name: str | None = None
    valid_from: str | None = None
    document_url: str | None = None
    is_draft: bool = False
    zones: list[PlanZone] = []
    infill_area: bool = False
    downtown_area: bool = False
    wms_url: str | None = None


# Zone symbol codes -> human-readable names
_POG_ZONE_NAMES: dict[str, str] = {
    "SW": "Strefa wielofunkcyjna z zabudowa mieszkaniowa wielorodzinna",
    "SJ": "Strefa wielofunkcyjna z zabudowa mieszkaniowa jednorodzinna",
    "SZ": "Strefa wielofunkcyjna z zabudowa zagrodowa",
    "SU": "Strefa uslugowa",
    "SH": "Strefa handlu wielkopowierzchniowego",
    "SP": "Strefa gospodarcza",
    "SR": "Strefa produkcji rolniczej",
    "SI": "Strefa infrastrukturalna",
    "SN": "Strefa zieleni i rekreacji",
    "SC": "Strefa cmentarzy",
    "SG": "Strefa gornicza",
    "SO": "Strefa otwarta",
    "SK": "Strefa komunikacyjna",
}
