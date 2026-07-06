import json
import hashlib
import time
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.services.cache_service import recommendation_cache
from app.services.profile_service import get_or_create_profile
from app.services.recommendation_engine import calculate_product_recommendations, recommend_bundles

logger = logging.getLogger(__name__)

def get_recommendations(
    db: Session,
    user_id: int,
    weather_report: Optional[dict] = None,
    knowledge_chunks: Optional[List[str]] = None,
    target_crop: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves recommendations for a user. Caches them for 10 minutes and
    persists recommendations in the user's profile history.
    """
    # 1. Compute Cache Key
    # Unique representation based on inputs
    weather_key = json.dumps(weather_report, sort_keys=True) if weather_report else "no_weather"
    knowledge_key = "".join(sorted(knowledge_chunks)) if knowledge_chunks else "no_knowledge"
    input_str = f"user_{user_id}|||weather_{weather_key}|||knowledge_{knowledge_key}|||crop_{target_crop or ''}"
    cache_key = hashlib.md5(input_str.encode("utf-8")).hexdigest()

    # 2. Check Cache
    cached_val = recommendation_cache.get(cache_key)
    if cached_val is not None:
        sync_recommendations_to_profile(db, user_id, cached_val)
        return cached_val

    # 3. Compute recommendations and bundles
    products = calculate_product_recommendations(
        db=db,
        user_id=user_id,
        weather_report=weather_report,
        knowledge_chunks=knowledge_chunks,
        target_crop=target_crop
    )
    
    bundles = recommend_bundles(
        db=db,
        user_id=user_id,
        recommended_products=products
    )

    results = {
        "recommendations": products[:8],  # Return top 8 products
        "bundles": bundles
    }

    # 4. Sync recommendations to user profile database
    sync_recommendations_to_profile(db, user_id, results)

    # 5. Set Cache
    recommendation_cache.set(cache_key, results, 10 * 60) # 10 minutes

    return results

def sync_recommendations_to_profile(db: Session, user_id: int, results: dict):
    """
    Saves a log of the top recommendations in the UserProfile.
    """
    try:
        profile = get_or_create_profile(db, user_id)
        
        recs_history = list(profile.previous_ai_recommendations or [])
        timestamp = time.time()
        
        # Build simple recommendation logs
        log_entry = {
            "timestamp": timestamp,
            "top_products": [p["name"] for p in results["recommendations"][:3]],
            "bundles": [b["bundle_name"] for b in results["bundles"]]
        }
        
        recs_history.insert(0, log_entry)
        profile.previous_ai_recommendations = recs_history[:5]  # Limit to 5 logs
        
        db.add(profile)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to sync recommendations to profile: {e}")
