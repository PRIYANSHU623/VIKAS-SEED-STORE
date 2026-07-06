from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from typing import Any, Dict, List

def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
    """
    Retrieve user profile. If it does not exist, create it with default values.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(
            user_id=user_id,
            preferred_language="en",
            preferred_crops=[],
            favourite_brands=[],
            budget=None,
            frequently_purchased_products=[],
            farm_location=None,
            soil_type=None,
            weather_location=None,
            previous_ai_recommendations=[],
            last_viewed_products=[]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def save_preference(db: Session, user_id: int, key: str, value: Any) -> UserProfile:
    """
    Save or append a single preference key.
    """
    profile = get_or_create_profile(db, user_id)
    if hasattr(profile, key):
        current_val = getattr(profile, key)
        if isinstance(current_val, list):
            if isinstance(value, list):
                new_list = list(current_val)
                for item in value:
                    if item not in new_list:
                        new_list.append(item)
                setattr(profile, key, new_list)
            else:
                new_list = list(current_val)
                if value not in new_list:
                    new_list.append(value)
                setattr(profile, key, new_list)
        else:
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
    return profile

def update_preference(db: Session, user_id: int, updates: Dict[str, Any]) -> UserProfile:
    """
    Update multiple preference keys.
    """
    profile = get_or_create_profile(db, user_id)
    for key, value in updates.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile

def load_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Load user preferences as a dictionary.
    """
    profile = get_or_create_profile(db, user_id)
    return {
        "preferred_language": profile.preferred_language,
        "preferred_crops": profile.preferred_crops,
        "favourite_brands": profile.favourite_brands,
        "budget": profile.budget,
        "frequently_purchased_products": profile.frequently_purchased_products,
        "farm_location": profile.farm_location,
        "soil_type": profile.soil_type,
        "weather_location": profile.weather_location,
        "previous_ai_recommendations": profile.previous_ai_recommendations,
        "last_viewed_products": profile.last_viewed_products
    }

def build_user_profile(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Build user profile data (returns preferences dictionary).
    """
    return load_preferences(db, user_id)

def build_user_profile_summary(db: Session, user_id: int) -> str:
    """
    Build a textual summary of user preferences for inclusion in the AI context.
    """
    prefs = load_preferences(db, user_id)
    summary_parts = []
    if prefs.get("preferred_language"):
        summary_parts.append(f"Preferred Language: {prefs['preferred_language']}")
    if prefs.get("preferred_crops"):
        crops = [c for c in prefs["preferred_crops"] if c]
        if crops:
            summary_parts.append(f"Preferred Crops: {', '.join(crops)}")
    if prefs.get("favourite_brands"):
        brands = [b for b in prefs["favourite_brands"] if b]
        if brands:
            summary_parts.append(f"Favourite Brands: {', '.join(brands)}")
    if prefs.get("budget"):
        summary_parts.append(f"Budget/Price Limit: INR {prefs['budget']}")
    if prefs.get("farm_location"):
        summary_parts.append(f"Farm Location: {prefs['farm_location']}")
    if prefs.get("soil_type"):
        summary_parts.append(f"Soil Type: {prefs['soil_type']}")
    if prefs.get("weather_location"):
        summary_parts.append(f"Weather Location: {prefs['weather_location']}")
    if prefs.get("frequently_purchased_products"):
        frequent_items = [
            p.get("name", str(p)) if isinstance(p, dict) else str(p)
            for p in prefs["frequently_purchased_products"]
            if p
        ]
        if frequent_items:
            summary_parts.append(f"Frequently Purchased Products: {', '.join(frequent_items)}")
    if prefs.get("last_viewed_products"):
        viewed_items = [
            p.get("name", str(p)) if isinstance(p, dict) else str(p)
            for p in prefs["last_viewed_products"]
            if p
        ]
        if viewed_items:
            summary_parts.append(f"Last Viewed Products: {', '.join(viewed_items)}")
            
    if not summary_parts:
        return "No preferences set yet."
    return "\n".join(summary_parts)
