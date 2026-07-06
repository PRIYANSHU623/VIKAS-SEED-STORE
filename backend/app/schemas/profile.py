from pydantic import BaseModel
from typing import List, Optional, Any

class UserProfileBase(BaseModel):
    preferred_language: Optional[str] = "en"
    preferred_crops: Optional[List[str]] = []
    favourite_brands: Optional[List[str]] = []
    budget: Optional[float] = None
    frequently_purchased_products: Optional[List[Any]] = []
    farm_location: Optional[str] = None
    soil_type: Optional[str] = None
    weather_location: Optional[str] = None
    previous_ai_recommendations: Optional[List[Any]] = []
    last_viewed_products: Optional[List[Any]] = []

class UserProfileCreate(UserProfileBase):
    user_id: int

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
