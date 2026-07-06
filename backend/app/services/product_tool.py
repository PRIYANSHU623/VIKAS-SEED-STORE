import json
import re
from google import genai
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY
from app.models.product import Product
from app.services.cache_service import product_cache

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are an Agricultural Product Filter Extractor.

Convert the user's request into JSON.

Available categories:
- seeds
- fertilizers
- pesticides
- herbicides

Available seasons:
- kharif
- rabi
- zaid

Available kinds:
- paddy
- wheat
- maize
- cotton
- mustard
- vegetable

Rules:

1. rainy season = kharif
2. monsoon = kharif
3. rice = paddy
4. wheat = wheat
5. If price mentioned:
   "under 2500"
   "below 2500"
   => max_price

Return ONLY JSON.

Example:

{
  "category":"seeds",
  "kind":"paddy",
  "season":"kharif",
  "max_price":2500
}
"""


def extract_filters_rule_based(question: str) -> dict:
    """
    Rule-based local keyword matcher to extract product filters without Gemini.
    """
    filters = {}
    lower_q = question.lower()
    
    # 1. Categories
    if "seed" in lower_q:
        filters["category"] = "seeds"
    elif "fertilizer" in lower_q or " खाद" in lower_q:
        filters["category"] = "fertilizers"
    elif "pesticide" in lower_q or "कीटनाशक" in lower_q:
        filters["category"] = "pesticides"
    elif "herbicide" in lower_q or "खरपतवार" in lower_q:
        filters["category"] = "herbicides"
        
    # 2. Seasons
    if "kharif" in lower_q or "monsoon" in lower_q or "rainy" in lower_q:
        filters["season"] = "kharif"
    elif "rabi" in lower_q or "winter" in lower_q:
        filters["season"] = "rabi"
    elif "zaid" in lower_q or "summer" in lower_q:
        filters["season"] = "zaid"
        
    # 3. Kinds
    for k in ["paddy", "rice", "wheat", "maize", "cotton", "mustard", "vegetable"]:
        if k in lower_q:
            filters["kind"] = "paddy" if k == "rice" else k
            break
            
    # 4. Brands
    for b in ["mahadhan", "syngenta", "vikas", "bayer", "pioneer"]:
        if b in lower_q:
            filters["brand"] = b
            break

    # 5. Price
    # Matches: under 2500, below 2500, max 2500, ₹2500, rs 2500
    price_match = re.search(r"(?:under|below|less than|within|₹|rs\.?|max)\s*(\d+)", lower_q)
    if price_match:
        filters["max_price"] = float(price_match.group(1))
        
    return filters


def extract_filters(question: str) -> dict:
    """
    Legacy Gemini-based filter extraction.
    """
    try:
        from app.services.gemini_service import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=[
                SYSTEM_PROMPT,
                question
            ]
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)
    except Exception:
        return {}
    
    
def run(question: str, db: Session, filters: dict = None):
    """
    Product search tool. Uses pre-extracted planner filters if available,
    otherwise falls back to rule-based or Gemini-based extraction.
    Caches the results.
    """
    # 1. Resolve filters
    if filters is None:
        # Check rule-based first
        filters = extract_filters_rule_based(question)
        if not filters:
            # Fallback to Gemini if rule-based returns empty (legacy path)
            filters = extract_filters(question)

    # 2. Check Cache
    cache_key = json.dumps(filters, sort_keys=True)
    cached_val = product_cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    # 3. Query DB
    query = db.query(Product)

    if filters.get("category"):
        query = query.filter(
            Product.category.ilike(filters["category"])
        )

    if filters.get("kind"):
        query = query.filter(
            Product.kind.ilike(f"%{filters['kind']}%")
        )

    if filters.get("season"):
        query = query.filter(
            Product.season.ilike(f"%{filters['season']}%")
        )

    if filters.get("brand"):
        query = query.filter(
            Product.brand.ilike(f"%{filters['brand']}%")
        )

    if filters.get("max_price"):
        query = query.filter(
            Product.price <= filters["max_price"]
        )

    if filters.get("min_price"):
        query = query.filter(
            Product.price >= filters["min_price"]
        )

    if filters.get("in_stock"):
        query = query.filter(
            Product.stock > 0
        )

    products = query.all()

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "kind": p.kind,
            "season": p.season,
            "price": p.price,
            "stock": p.stock,
            "description": p.description,
            "image_url": p.image_url
        })

    res_dict = {
        "tool": "product",
        "success": True,
        "data": {
            "filters": filters,
            "count": len(result),
            "products": result
        }
    }

    # 4. Set Cache
    product_cache.set(cache_key, res_dict, 10 * 60) # 10 minutes

    return res_dict