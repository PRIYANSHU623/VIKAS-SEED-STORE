from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any

class PlannerStep(BaseModel):
    model_config = {"extra": "forbid"}
    tool: Literal["product", "knowledge", "order", "weather", "scanner", "farm_plan", "calendar"]
    filters: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    input: Optional[str] = None

class PlannerResponse(BaseModel):
    model_config = {"extra": "forbid"}
    steps: List[PlannerStep]
