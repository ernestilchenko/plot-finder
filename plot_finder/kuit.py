from pydantic import BaseModel


class KUIT(BaseModel):
    """Krajowa Integracja Uzbrojenia Terenu — underground utility infrastructure."""

    has_data: bool = False
    water: bool = False
    sewage: bool = False
    gas: bool = False
    power: bool = False
    telecom: bool = False
    heating: bool = False
    wms_url: str | None = None
