from pydantic import BaseModel


class RiskInfo(BaseModel):
    risk_type: str
    name: str
    level: str
    is_at_risk: bool
    description: str
    color: str


class RiskReport(BaseModel):
    risks: list[RiskInfo] = []
    total_risks: int = 0
