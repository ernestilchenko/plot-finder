from pydantic import BaseModel


class AirQuality(BaseModel):
    aqi: int
    aqi_label: str
    co: float
    no: float
    no2: float
    o3: float
    so2: float
    pm2_5: float
    pm10: float
    nh3: float
