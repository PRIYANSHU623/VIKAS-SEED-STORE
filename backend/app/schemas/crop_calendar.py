from pydantic import BaseModel
from typing import List, Optional, Any

class CalendarEvent(BaseModel):
    stage: str
    days_offset: int
    scheduled_date: str
    status: str  # "pending", "completed", "current"
    description: str

class CropCalendarResponse(BaseModel):
    crop: str
    start_date: str
    stages: List[CalendarEvent]
    weather_warnings: List[str]
