from pydantic import BaseModel


class MPZP(BaseModel):
    has_plan: bool = False
    zone_symbol: str | None = None
    zone_name: str | None = None
    plan_name: str | None = None
    resolution: str | None = None
    resolution_date: str | None = None
    publication: str | None = None
    effective_date: str | None = None
    wms_url: str | None = None
