from pydantic import BaseModel


class Place(BaseModel):
    name: str | None = None
    kind: str
    lat: float
    lon: float
    distance_m: float
