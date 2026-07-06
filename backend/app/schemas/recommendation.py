from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class RecommendationItem(BaseModel):
    product_id: int
    name: str
    brand: str
    category: str
    price: float
    score: float
    reason: str

class BundleRecommendation(BaseModel):
    bundle_name: str
    crop: str
    items: List[Dict[str, Any]]
    estimated_cost: float
    reason: str
    alternatives: Dict[str, List[Dict[str, Any]]]

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    bundles: List[BundleRecommendation]
