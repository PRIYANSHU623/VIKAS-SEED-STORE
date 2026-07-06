from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class SuitabilityDetails(BaseModel):
    score: float
    suitable: bool
    reason: str

class SuitabilityMetrics(BaseModel):
    spraying: SuitabilityDetails
    irrigation: SuitabilityDetails
    sowing: SuitabilityDetails
    harvest: SuitabilityDetails
    fertilizer: SuitabilityDetails

class RiskMetrics(BaseModel):
    heavy_rainfall: str
    frost: str
    heat_stress: str

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    humidity: float
    wind_speed: float
    rain_probability: float
    forecast: str
    recommendation: str
    suitability: SuitabilityMetrics
    risks: RiskMetrics
