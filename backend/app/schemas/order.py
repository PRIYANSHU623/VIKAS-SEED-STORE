from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None


from app.schemas.user import UserResponse
from app.schemas.product import ProductResponse


class OrderResponse(OrderBase):
    id: int
    user_id: int
    total_price: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
