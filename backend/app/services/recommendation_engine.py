import logging
import hashlib
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.models.product import Product
from app.models.order import Order
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# Unique product traits dictionary for Task 6
PRODUCT_TRAITS = {
    "arize": ["High yielding hybrid seed", "Performs well in rainy Kharif season", "Excellent grain weight", "High disease resistance"],
    "damini": ["Early maturity variety", "Suitable for medium rainfall zones", "High germination uniformity", "Highly popular among local farmers"],
    "mahadhan": ["Balanced nutrient absorption", "Improves overall crop resistance", "High water solubility for foliar sprays", "Enriched with secondary micro-nutrients"],
    "syngenta": ["Premium certified brand variety", "Excellent cold and rust tolerance", "Protects against early vegetative pests", "Uniform crop establishment"],
    "bayer": ["Advanced systemic crop protection", "Low residue eco-friendly formulation", "Quick action contact control", "Long-lasting field protection"],
    "neem": ["100% organic neem formulation", "Improves soil microbial health", "Natural repellent properties", "Safe for beneficial insects"]
}

def generate_product_reason(p: Product, budget: Optional[float], target_crop: Optional[str], weather_report: Optional[dict], profile: UserProfile) -> str:
    """
    Task 6: Generates a unique, product-specific reason list formatted as bullet points.
    """
    traits = []
    p_name_lower = p.name.lower()
    p_brand_lower = (p.brand or "").lower()

    # 1. Match specific traits from dictionary
    matched = False
    for brand_key, brand_traits in PRODUCT_TRAITS.items():
        if brand_key in p_name_lower or brand_key in p_brand_lower:
            traits.extend(brand_traits[:2])
            matched = True
            break
            
    if not matched:
        # Default trait fallback by category
        cat = p.category.lower()
        if "seed" in cat:
            traits.extend(["High-yielding certified seed variety", "Tested for maximum germination rate"])
        elif "fertilizer" in cat:
            traits.extend(["Supplies nitrogen and phosphorus", "Aids quick root development"])
        elif "pesticide" in cat:
            traits.extend(["Broad-spectrum pest control", "Protects crop during critical growth phases"])
        else:
            traits.extend(["Enhances yield output quality", "Provides weed-free growth environment"])

    # 2. Add budget and preference match reasons
    if budget and p.price <= budget:
        traits.append(f"Fits your ₹{int(budget)} budget limit")
    else:
        traits.append("Cost-effective cultivation choice")

    p_kind = (p.kind or "").lower()
    if target_crop and target_crop.lower() in p_kind:
        traits.append(f"Ideal for {target_crop.capitalize()} crop schedule")
    elif profile.preferred_crops and any(c.lower() in p_kind for c in profile.preferred_crops):
        traits.append("Matches your crop preferences")

    # 3. Weather check
    if weather_report and "suitability" in weather_report:
        cat = p.category.lower()
        suit = weather_report["suitability"]
        if "seed" in cat and suit.get("sowing", {}).get("suitable"):
            traits.append("Favoured by current sowing forecast")
        elif "fertilizer" in cat and suit.get("fertilizer", {}).get("suitable"):
            traits.append("Safe to broadcast in current wind forecast")
        elif ("pesticide" in cat or "herbicide" in cat) and suit.get("spraying", {}).get("suitable"):
            traits.append("Optimal dry weather for spraying")

    # Deduplicate and return at most 4 bullets
    unique_traits = []
    for t in traits:
        if t not in unique_traits:
            unique_traits.append(t)

    return " • ".join(unique_traits[:4])


def calculate_product_recommendations(
    db: Session,
    user_id: int,
    weather_report: Optional[dict] = None,
    knowledge_chunks: Optional[List[str]] = None,
    target_crop: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Task 2: Weighted scoring algorithm with 8 sub-metrics:
    - Weather Suitability: 20%
    - Knowledge Relevance: 20%
    - Budget Match: 15%
    - Preferred Crop: 15%
    - Preferred Brand: 10%
    - Popularity: 10%
    - Stock Availability: 5%
    - Customer Purchase History: 5%
    
    Task 1: Removes duplicate products using Product ID.
    Task 6: Product-specific reasons.
    Task 9: Recommendation confidence.
    """
    # 1. Fetch User Profile & Orders
    from app.services.profile_service import get_or_create_profile
    profile = get_or_create_profile(db, user_id)
    
    preferred_crops = profile.preferred_crops or []
    if target_crop and target_crop not in preferred_crops:
        preferred_crops = [target_crop] + list(preferred_crops)
        
    favourite_brands = profile.favourite_brands or []
    budget = profile.budget

    # Fetch user's order history for Customer Purchase History (5%)
    user_purchased_pids = set()
    try:
        user_orders = db.query(Order).filter(Order.user_id == user_id).all()
        for o in user_orders:
            pid = getattr(o, "product_id", None)
            if pid:
                user_purchased_pids.add(pid)
    except Exception as e:
        logger.error(f"Error reading user orders: {e}")

    # Fetch global popularity map
    popularity_map = {}
    try:
        orders = db.query(Order).all()
        for o in orders:
            pid = getattr(o, "product_id", None)
            if pid:
                popularity_map[pid] = popularity_map.get(pid, 0) + 1
    except Exception as e:
         logger.error(f"Order popularity mapping failed: {e}")

    max_orders = max(popularity_map.values()) if popularity_map else 1

    # Compile knowledge chunks to check keyword relevance
    knowledge_text = ""
    if knowledge_chunks:
        knowledge_text = " ".join(knowledge_chunks).lower()

    # Fetch all products
    products = db.query(Product).all()
    
    # Task 1: Deduplicate list by product ID
    seen_pids = set()
    unique_products = []
    for p in products:
        if p.id not in seen_pids:
            unique_products.append(p)
            seen_pids.add(p.id)

    recommended_list = []

    for p in unique_products:
        # A. Preferred Crop Score (15%)
        crop_score = 0.0
        p_kind = (p.kind or "").lower()
        p_name = (p.name or "").lower()
        if preferred_crops:
            for c in preferred_crops:
                if c.lower() in p_kind or c.lower() in p_name:
                    crop_score = 1.0
                    break
        elif target_crop and target_crop.lower() in p_kind:
            crop_score = 1.0

        # B. Preferred Brand Score (10%)
        brand_score = 0.0
        p_brand = (p.brand or "").lower()
        if favourite_brands:
            for b in favourite_brands:
                if b.lower() in p_brand:
                    brand_score = 1.0
                    break

        # C. Budget Score (15%)
        budget_score = 1.0
        if budget and budget > 0:
            if p.price <= budget:
                budget_score = 1.0
            elif p.price <= budget * 1.5:
                budget_score = 0.5
            else:
                budget_score = 0.0

        # D. Stock Availability Score (5%)
        stock_score = 1.0 if p.stock and p.stock > 0 else 0.0

        # E. Popularity Score (10%)
        orders_count = popularity_map.get(p.id, 0)
        popularity_score = float(orders_count) / max_orders

        # F. Customer Purchase History Score (5%)
        history_score = 1.0 if p.id in user_purchased_pids else 0.0

        # G. Knowledge Relevance Score (20%)
        knowledge_score = 0.0
        if knowledge_text:
            p_name_lower = p.name.lower()
            p_brand_lower = p.brand.lower() if p.brand else ""
            p_kind_lower = p.kind.lower() if p.kind else ""
            if p_name_lower in knowledge_text or (p_brand_lower and p_brand_lower in knowledge_text) or (p_kind_lower and p_kind_lower in knowledge_text):
                knowledge_score = 1.0
            elif p.category.lower() in knowledge_text:
                knowledge_score = 0.5

        # H. Weather Suitability Score (20%)
        weather_score = 1.0
        if weather_report and "suitability" in weather_report:
            cat = p.category.lower()
            suitability_report = weather_report["suitability"]
            if "seed" in cat:
                weather_score = suitability_report.get("sowing", {}).get("score", 80.0) / 100.0
            elif "fertilizer" in cat:
                weather_score = suitability_report.get("fertilizer", {}).get("score", 80.0) / 100.0
            elif "pesticide" in cat or "herbicide" in cat:
                weather_score = suitability_report.get("spraying", {}).get("score", 80.0) / 100.0

        # 2. Weighted Score Math (out of 100.0)
        final_score = (
            (weather_score * 0.20) +
            (knowledge_score * 0.20) +
            (budget_score * 0.15) +
            (crop_score * 0.15) +
            (brand_score * 0.10) +
            (popularity_score * 0.10) +
            (stock_score * 0.05) +
            (history_score * 0.05)
        )
        
        # 3. Add tiny high-precision micro-adjustment to prevent duplicate scores (Task 2)
        # Combines a hash of product name + price fraction to uniquely differentiate
        name_hash = int(hashlib.md5(p.name.encode('utf-8')).hexdigest()[:6], 16) % 1000
        micro_adjustment = (name_hash * 1e-6) + ((p.price % 100) * 1e-8)
        sorting_score = final_score + micro_adjustment

        # 4. Task 6: Product-Specific Reason
        reason_str = generate_product_reason(p, budget, target_crop, weather_report, profile)

        # 5. Task 9: Confidence score
        confidence = "Medium"
        if weather_score >= 0.75 and knowledge_score >= 0.5 and p.stock and p.stock > 10:
            confidence = "High"
        elif weather_score < 0.40 or (p.stock is not None and p.stock == 0):
            confidence = "Low"

        recommended_list.append({
            "product_id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "price": p.price,
            "score": round(final_score * 100, 2),
            "sorting_score": sorting_score,
            "reason": reason_str,
            "stock": p.stock,
            "kind": p.kind,
            "image_url": p.image_url,
            "confidence": confidence,
            "weather_score": weather_score
        })

    # Sort descending by sorting_score
    recommended_list.sort(key=lambda x: x["sorting_score"], reverse=True)
    return recommended_list


def recommend_bundles(
    db: Session,
    user_id: int,
    recommended_products: List[Dict[str, Any]],
    weather_report: Optional[dict] = None
) -> List[Dict[str, Any]]:
    """
    Task 8: Cultivation Packages (Bundles) improvements.
    - Choose products that complement each other.
    - Avoid duplicate brands when possible.
    - Computes: Total Cost, Average Score, Yield Benefit, and Weather Compatibility.
    - Task 1: Enforces no duplicate products.
    """
    crops = set()
    for r in recommended_products:
        kind = r.get("kind")
        if kind:
            crops.add(kind.strip().capitalize())

    if not crops:
        crops = {"Paddy", "Wheat"}

    bundles = []

    for crop in crops:
        crop_lower = crop.lower()
        
        # Filter matching inputs
        seeds = [p for p in recommended_products if "seed" in p["category"].lower() and (p["kind"] and crop_lower in p["kind"].lower())]
        fertilizers = [p for p in recommended_products if "fertilizer" in p["category"].lower() and (not p["kind"] or crop_lower in p["kind"].lower() or p["kind"].lower() == "all")]
        pesticides = [p for p in recommended_products if "pesticide" in p["category"].lower() and (not p["kind"] or crop_lower in p["kind"].lower() or p["kind"].lower() == "all")]
        herbicides = [p for p in recommended_products if "herbicide" in p["category"].lower() and (not p["kind"] or crop_lower in p["kind"].lower() or p["kind"].lower() == "all")]

        # Category fallbacks
        if not seeds:
            seeds = [p for p in recommended_products if "seed" in p["category"].lower()]
        if not fertilizers:
            fertilizers = [p for p in recommended_products if "fertilizer" in p["category"].lower()]
        if not pesticides:
            pesticides = [p for p in recommended_products if "pesticide" in p["category"].lower()]
        if not herbicides:
            herbicides = [p for p in recommended_products if "herbicide" in p["category"].lower()]

        if seeds and fertilizers:
            # Enforce brand deduplication and product uniqueness
            selected_items = []
            used_brands = set()
            used_pids = set()

            def add_to_bundle(candidates, category_label):
                for p in candidates:
                    if p["product_id"] not in used_pids:
                        p_brand = p["brand"] or "Generic"
                        # Try to avoid brand duplicates if possible
                        if p_brand not in used_brands or len(used_brands) >= len(candidates):
                            selected_items.append({
                                "product_id": p["product_id"],
                                "name": p["name"],
                                "category": category_label,
                                "price": p["price"],
                                "score": p["score"],
                                "weather_score": p.get("weather_score", 0.8),
                                "brand": p["brand"]
                            })
                            used_brands.add(p_brand)
                            used_pids.add(p["product_id"])
                            return

            add_to_bundle(seeds, "Seed")
            add_to_bundle(fertilizers, "Fertilizer")
            if pesticides:
                add_to_bundle(pesticides, "Pesticide")
            if herbicides:
                add_to_bundle(herbicides, "Herbicide")

            # 1. Total Cost
            total_cost = round(sum(item["price"] for item in selected_items), 2)
            
            # 2. Average Score
            avg_score = round(sum(item["score"] for item in selected_items) / len(selected_items), 1)

            # 3. Estimated Yield Benefit
            # Base crop yields benefit
            yield_benefit = 15.0
            if crop_lower == "paddy":
                yield_benefit += 10.0
            elif crop_lower == "wheat":
                yield_benefit += 8.0
            if avg_score > 80.0:
                yield_benefit += 5.0
            yield_benefit_str = f"{round(yield_benefit, 1)}% Increase"

            # 4. Weather Compatibility
            weather_comp_val = sum(item["weather_score"] for item in selected_items) / len(selected_items)
            weather_comp_pct = int(weather_comp_val * 100)
            weather_status = "Excellent" if weather_comp_pct >= 80 else "Good" if weather_comp_pct >= 50 else "Poor"
            weather_comp_str = f"{weather_comp_pct}% ({weather_status})"

            # Alternatives
            alternatives = {
                "seeds": [{"product_id": s["product_id"], "name": s["name"], "price": s["price"]} for s in seeds if s["product_id"] not in used_pids][:2],
                "fertilizers": [{"product_id": f["product_id"], "name": f["name"], "price": f["price"]} for f in fertilizers if f["product_id"] not in used_pids][:2],
                "pesticides": [{"product_id": p["product_id"], "name": p["name"], "price": p["price"]} for p in pesticides if p["product_id"] not in used_pids][:2],
                "herbicides": [{"product_id": h["product_id"], "name": h["name"], "price": h["price"]} for h in herbicides if h["product_id"] not in used_pids][:2]
            }

            bundles.append({
                "bundle_name": f"Premium {crop} Cultivation Package",
                "crop": crop,
                "items": [
                    {"product_id": x["product_id"], "name": x["name"], "category": x["category"], "price": x["price"]}
                    for x in selected_items
                ],
                "estimated_cost": total_cost,
                "average_score": avg_score,
                "yield_benefit": yield_benefit_str,
                "weather_compatibility": weather_compatibility_str(selected_items),
                "reason": f"Complete synergistic solution for high-yielding {crop} cultivation. The package boasts {weather_comp_str} weather compatibility and an estimated yield boost of {yield_benefit_str}.",
                "alternatives": alternatives
            })

    return bundles

def weather_compatibility_str(items: List[dict]) -> str:
    weather_comp_val = sum(item["weather_score"] for item in items) / len(items)
    weather_comp_pct = int(weather_comp_val * 100)
    weather_status = "Excellent" if weather_comp_pct >= 80 else "Good" if weather_comp_pct >= 50 else "Poor"
    return f"{weather_comp_pct}% ({weather_status})"
