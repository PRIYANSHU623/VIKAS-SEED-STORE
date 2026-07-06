from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class FarmPlanCreate(BaseModel):
    crop: str
    season: Optional[str] = "Kharif"

class FarmPlanResponse(BaseModel):
    id: int
    user_id: int
    crop: str
    season: str
    plan_json: Dict[str, Any]
    estimated_cost: float
    expected_yield: str
    created_at: datetime

    class Config:
        from_attributes = True
