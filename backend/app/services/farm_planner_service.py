import json
import hashlib
import logging
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY
from app.models.farm_plan import FarmPlan
from app.services.cache_service import planner_cache  # reuse simple cache or add direct helper
from app.services.weather_service import get_weather
from app.services.rag_service import retrieve_chunks
from app.services.recommendation_service import get_recommendations
from app.services.profile_service import build_user_profile_summary

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

FARM_PLAN_SYSTEM_PROMPT = """
You are the AI Farm Planner for KrishiSathi (Vikas Beej Bhandar).
Your task is to analyze the crop and generate a comprehensive, highly personalized Farm Plan for the farmer.

You must return a structured JSON plan matching the requested fields exactly.

You will be provided with:
1. Target Crop name
2. Farmer Profile preferences
3. Real-time Weather details at their location
4. Relevant RAG Knowledge Base guide chunks
5. Top recommended products from our store catalog

Instructions:
- Synthesize all input data to compile a cohesive, actionable plan.
- Ensure the fertilizer, herbicide, and pesticide schedules specify timing relative to sowing day (e.g., Day 0, Day 20, Day 45).
- Under 'recommended_store_products', only include actual products from the provided store recommendation catalog.
- Under 'alternative_products', include alternatives from the catalog.
- Estimate the total cost (seed + fertilizers + inputs + standard labor) as a number under 'estimated_cost'.
- Specify 'expected_yield' (e.g., '22-25 quintals per acre') and 'harvest_time' (e.g., '120 Days').
"""

# Dynamic Pydantic schema for Gemini Developer API compatibility
class FarmPlanSchema:
    @staticmethod
    def get_schema() -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "crop": {"type": "STRING"},
                "suitable_variety": {"type": "STRING"},
                "recommended_seed": {"type": "STRING"},
                "suitable_season": {"type": "STRING"},
                "suitable_soil": {"type": "STRING"},
                "required_water": {"type": "STRING"},
                "fertilizer_schedule": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "day": {"type": "INTEGER"},
                            "fertilizer": {"type": "STRING"},
                            "quantity": {"type": "STRING"}
                        },
                        "required": ["day", "fertilizer", "quantity"]
                    }
                },
                "herbicide_schedule": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "day": {"type": "INTEGER"},
                            "herbicide": {"type": "STRING"},
                            "quantity": {"type": "STRING"}
                        },
                        "required": ["day", "herbicide", "quantity"]
                    }
                },
                "pesticide_schedule": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "day": {"type": "INTEGER"},
                            "pesticide": {"type": "STRING"},
                            "quantity": {"type": "STRING"}
                        },
                        "required": ["day", "pesticide", "quantity"]
                    }
                },
                "disease_prevention_tips": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "weather_risks": {"type": "STRING"},
                "estimated_cost": {"type": "NUMBER"},
                "expected_yield": {"type": "STRING"},
                "recommended_store_products": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "category": {"type": "STRING"},
                            "name": {"type": "STRING"},
                            "price": {"type": "NUMBER"}
                        },
                        "required": ["category", "name", "price"]
                    }
                },
                "alternative_products": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "category": {"type": "STRING"},
                            "name": {"type": "STRING"},
                            "price": {"type": "NUMBER"}
                        },
                        "required": ["category", "name", "price"]
                    }
                },
                "harvest_time": {"type": "STRING"}
            },
            "required": [
                "crop", "suitable_variety", "recommended_seed", "suitable_season",
                "suitable_soil", "required_water", "fertilizer_schedule",
                "herbicide_schedule", "pesticide_schedule", "disease_prevention_tips",
                "weather_risks", "estimated_cost", "expected_yield",
                "recommended_store_products", "alternative_products", "harvest_time"
            ]
        }


def generate_farm_plan(db: Session, user_id: int, crop: str) -> dict:
    """
    Orchestrates inputs from weather, knowledge RAG, and store catalogs to construct
    and cache a complete farm plan for the user.
    """
    crop_normalized = crop.strip().capitalize()
    
    # 1. Check Cache
    cache_key = f"farmplan_{user_id}_{hashlib.md5(crop_normalized.encode('utf-8')).hexdigest()}"
    cached_val = planner_cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    # 2. Gather context inputs
    profile_summary = build_user_profile_summary(db, user_id)
    
    # Get weather
    try:
        weather_report = get_weather(db, user_id)
        if "location_required" in weather_report:
            weather_report = {"location": "Ludhiana, Punjab (Default)", "forecast": "Clear Sky", "temperature": 28}
    except Exception:
        weather_report = {"location": "Punjab", "forecast": "Partly Cloudy"}
        
    # Get RAG crop knowledge
    try:
        knowledge_chunks = retrieve_chunks(f"cultivation guide and practices for growing {crop_normalized}")
    except Exception:
        knowledge_chunks = []
        
    # Get product recommendations
    try:
        recs = get_recommendations(db, user_id, weather_report, knowledge_chunks, target_crop=crop_normalized)
        store_catalog = recs.get("recommendations", [])
    except Exception:
        store_catalog = []

    prompt = f"""
Target Crop: {crop_normalized}

User Profile Preferences:
--------------------
{profile_summary}
--------------------

Current Field Weather Details:
--------------------
{json.dumps(weather_report, indent=2)}
--------------------

Agricultural RAG Guidance:
--------------------
{json.dumps(knowledge_chunks, indent=2)}
--------------------

Available Store Catalog Products:
--------------------
{json.dumps(store_catalog[:6], indent=2)}
--------------------

Please construct the complete farming plan:
"""
    try:
        from app.services.gemini_service import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=[
                FARM_PLAN_SYSTEM_PROMPT,
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FarmPlanSchema.get_schema(),
                temperature=0.0
            )
        )
        plan_data = json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Failed to generate AI Farm Plan: {e}")
        # Local offline fallback plan
        plan_data = get_offline_fallback_plan(crop_normalized, store_catalog)

    # 3. Save to database
    db_plan = FarmPlan(
        user_id=user_id,
        crop=crop_normalized,
        season=plan_data.get("suitable_season", "Kharif"),
        plan_json=plan_data,
        estimated_cost=float(plan_data.get("estimated_cost", 15000)),
        expected_yield=plan_data.get("expected_yield", "20 quintals/acre")
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    plan_data["id"] = db_plan.id
    plan_data["user_id"] = db_plan.user_id

    # 4. Cache plan for 15 minutes
    planner_cache.set(cache_key, plan_data, 15 * 60)

    return plan_data


def get_offline_fallback_plan(crop: str, catalog: list) -> dict:
    """
    Robust local rule-based fallback farm plan when Gemini API fails.
    """
    logger.warning(f"Generating offline fallback farm plan for {crop}")
    
    seeds = [p for p in catalog if "seed" in p["category"].lower()][:2]
    ferts = [p for p in catalog if "fertilizer" in p["category"].lower()][:2]
    pests = [p for p in catalog if "pesticide" in p["category"].lower()][:2]
    
    seed_name = seeds[0]["name"] if seeds else f"Vikas Hybrid {crop} Seed"
    seed_price = seeds[0]["price"] if seeds else 950.0
    
    fert_name = ferts[0]["name"] if ferts else "Mahadhan NPK Fertilizer"
    fert_price = ferts[0]["price"] if ferts else 450.0

    pest_name = pests[0]["name"] if pests else "Neem Shield Pesticide"
    pest_price = pests[0]["price"] if pests else 350.0

    total_cost = seed_price + fert_price + pest_price + 8000 # include labor estimates
    
    return {
        "crop": crop,
        "suitable_variety": seed_name,
        "recommended_seed": seed_name,
        "suitable_season": "Kharif" if crop.lower() == "paddy" else "Rabi",
        "suitable_soil": "Alluvial clayey soil with good water retention.",
        "required_water": "Moderate to High irrigation schedule.",
        "fertilizer_schedule": [
            {"day": 0, "fertilizer": "DAP", "quantity": "50 kg/acre"},
            {"day": 25, "fertilizer": "Urea", "quantity": "40 kg/acre"},
            {"day": 50, "fertilizer": "Urea + Potash", "quantity": "40 kg/acre"}
        ],
        "herbicide_schedule": [
            {"day": 3, "herbicide": "Pre-emergence Herbicide", "quantity": "1 L/acre"}
        ],
        "pesticide_schedule": [
            {"day": 35, "pesticide": pest_name, "quantity": "500 ml/acre"}
        ],
        "disease_prevention_tips": [
            "Use certified clean seeds to prevent seed-borne blight.",
            "Maintain optimal field drainage to avoid root rot."
        ],
        "weather_risks": "Hold off sowing if heavy showers are expected within 48 hours.",
        "estimated_cost": total_cost,
        "expected_yield": "20-22 quintals per acre",
        "recommended_store_products": [
            {"category": "Seed", "name": seed_name, "price": seed_price},
            {"category": "Fertilizer", "name": fert_name, "price": fert_price}
        ],
        "alternative_products": [
            {"category": "Pesticide", "name": pest_name, "price": pest_price}
        ],
        "harvest_time": "120 Days"
    }
