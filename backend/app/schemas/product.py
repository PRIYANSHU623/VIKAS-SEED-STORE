from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ProductBase(BaseModel):
    name: str
    brand: Optional[str] = None
    category: str
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    stock: int = Field(..., ge=0)
    image_url: Optional[str] = None
    kind: Optional[str] = None
    season: Optional[str] = None
    
    # New onboarding fields
    manufacturer: Optional[str] = None
    net_quantity: Optional[str] = None
    batch_number: Optional[str] = None
    mfg_date: Optional[str] = None
    expiry_date: Optional[str] = None
    registration_number: Optional[str] = None
    ingredients: Optional[str] = None
    chemical_composition: Optional[str] = None
    usage_instructions: Optional[str] = None
    storage_instructions: Optional[str] = None
    safety_warnings: Optional[str] = None
    license_numbers: Optional[str] = None
    
    # JSON metadata, confidence scores, sources, and tags
    agricultural_metadata: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, Any]] = None
    sources: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    kind: Optional[str] = None
    season: Optional[str] = None
    
    # New onboarding fields
    manufacturer: Optional[str] = None
    net_quantity: Optional[str] = None
    batch_number: Optional[str] = None
    mfg_date: Optional[str] = None
    expiry_date: Optional[str] = None
    registration_number: Optional[str] = None
    ingredients: Optional[str] = None
    chemical_composition: Optional[str] = None
    usage_instructions: Optional[str] = None
    storage_instructions: Optional[str] = None
    safety_warnings: Optional[str] = None
    license_numbers: Optional[str] = None
    
    # JSON metadata, confidence scores, sources, and tags
    agricultural_metadata: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, Any]] = None
    sources: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True

