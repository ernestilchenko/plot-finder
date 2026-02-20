from pydantic import BaseModel


class NoiseSource(BaseModel):
    type: str
    name: str
    distance_km: float
    impact_db: float
    lat: float
    lon: float


class Noise(BaseModel):
    noise_level_db: float
    quality: str
    level: str
    description: str
    color: str
    sources: list[NoiseSource] = []
    data_source: str
