from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from typing import Dict, Any, Optional

def clean_string(s: Optional[str]) -> str:
    """Helper to lowercase and strip whitespace/special characters for robust matching."""
    if not s:
        return ""
    # Remove whitespace and punctuation/hyphens for fuzzy comparison
    return func.lower(func.regexp_replace(s, r'[\s\-_,\.]', '', 'g'))

def check_for_duplicate(db: Session, name: str, brand: str, weight: str) -> Dict[str, Any]:
    """
    Checks if a product with the same name, brand, and weight/volume exists in the database.
    Weight could be stored in net_quantity or as part of name/description. We check:
    - Name match (case-insensitive)
    - Brand match (case-insensitive)
    - Weight/net_quantity match (case-insensitive, ignoring spacing)
    """
    if not name:
        return {"duplicate_found": False}

    # Normalize inputs
    clean_name_input = name.lower().replace(" ", "").replace("-", "")
    clean_brand_input = (brand or "").lower().replace(" ", "").replace("-", "")
    clean_weight_input = (weight or "").lower().replace(" ", "").replace("-", "")

    # Query all products to find candidates
    products = db.query(Product).all()

    for p in products:
        p_name = p.name.lower().replace(" ", "").replace("-", "")
        p_brand = (p.brand or "").lower().replace(" ", "").replace("-", "")
        # Check net_quantity, or look in kind/description if net_quantity is empty
        p_weight = (p.net_quantity or "").lower().replace(" ", "").replace("-", "")
        
        # Fuzzy match Name + Brand
        name_match = (clean_name_input in p_name) or (p_name in clean_name_input)
        brand_match = (clean_brand_input == p_brand) or (not clean_brand_input and not p_brand)
        
        # Check weight match if weight is provided
        weight_match = True
        if clean_weight_input and p_weight:
            weight_match = (clean_weight_input == p_weight) or (clean_weight_input in p_weight) or (p_weight in clean_weight_input)
        elif clean_weight_input or p_weight:
            # One has weight and the other doesn't, let's treat it as potential duplicate but with lower priority
            weight_match = False

        if name_match and brand_match and weight_match:
            return {
                "duplicate_found": True,
                "message": "This product already exists.",
                "existing_product": {
                    "id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                    "category": p.category,
                    "price": p.price,
                    "stock": p.stock,
                    "net_quantity": p.net_quantity or weight
                }
            }

    return {"duplicate_found": False}
