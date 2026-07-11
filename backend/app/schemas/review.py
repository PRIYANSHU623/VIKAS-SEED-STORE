from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    product_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1)
    user_role: Optional[str] = None
    user_location: Optional[str] = None
    user_image: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=1)

class ReviewResponse(ReviewBase):
    id: int
    user_id: Optional[int] = None
    user_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
