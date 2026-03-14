from pydantic import BaseModel


class LandUse(BaseModel):
    """Land use classification from Krajowa Integracja Użytków Gruntowych."""

    has_data: bool = False
    plot_id: str | None = None
    area_ha: float | None = None
    use_code: str | None = None
    use_name: str | None = None
    registry_group: str | None = None
    wms_url: str | None = None


_LAND_USE_NAMES: dict[str, str] = {
    "R": "Grunty orne",
    "S": "Sady",
    "Ł": "Łąki trwałe",
    "Ps": "Pastwiska trwałe",
    "Ls": "Lasy",
    "Lz": "Grunty zadrzewione i zakrzewione",
    "B": "Tereny mieszkaniowe",
    "Ba": "Tereny przemysłowe",
    "Bi": "Inne tereny zabudowane",
    "Bp": "Zurbanizowane tereny niezabudowane",
    "Bz": "Tereny rekreacyjno-wypoczynkowe",
    "K": "Użytki kopalne",
    "dr": "Drogi",
    "Ti": "Inne tereny komunikacyjne",
    "Tk": "Użytki kolejowe",
    "W": "Grunty pod wodami",
    "Wm": "Grunty pod morskimi wodami wewnętrznymi",
    "Wp": "Grunty pod wodami powierzchniowymi płynącymi",
    "Ws": "Grunty pod wodami powierzchniowymi stojącymi",
    "N": "Nieużytki",
    "Tr": "Tereny różne",
    "E": "Grunty pod rowami",
}