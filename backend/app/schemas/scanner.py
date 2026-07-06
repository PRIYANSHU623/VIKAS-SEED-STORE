from pydantic import BaseModel
from typing import Optional

class ScannedProduct(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    crop_type: Optional[str] = None
    weight: Optional[str] = None
    mrp: Optional[float] = None
    description: Optional[str] = None