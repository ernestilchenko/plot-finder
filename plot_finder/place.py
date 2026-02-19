from pydantic import BaseModel


class Place(BaseModel):
    name: str | None = None
    kind: str
    lat: float
    lon: float
    distance_m: float
    walk_min: int = 0
    bike_min: int = 0
    car_min: int = 0
