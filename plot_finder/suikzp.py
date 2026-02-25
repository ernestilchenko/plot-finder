from __future__ import annotations

from pydantic import BaseModel


class SUIKZP(BaseModel):
    """Studium Uwarunkowan i Kierunkow Zagospodarowania Przestrzennego."""

    has_plan: bool = False
    plan_name: str | None = None
    resolution: str | None = None
    resolution_date: str | None = None
    plan_type: str | None = None
    legend_url: str | None = None
    document_url: str | None = None
    wms_url: str | None = None
