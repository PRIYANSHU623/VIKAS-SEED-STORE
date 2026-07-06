import json
import hashlib
import logging
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY
from app.schemas.planner import PlannerResponse
from app.services.profile_service import build_user_profile_summary
from app.services.rag_service import retrieve_chunks
from app.services.cache_service import planner_cache

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are the AI Planner for KrishiSathi (Vikas Beej Bhandar), an agricultural e-commerce and advisory platform.

Your task is to analyze the farmer's question and determine a sequence of tool execution steps to gather all required information. You must also perform all entity extraction, parameter extraction, and filter detection for downstream tools.

Available Tools:

1. "product":
   - Use this to search, filter, or recommend agricultural products (seeds, fertilizers, pesticides, herbicides).
   - You MUST extract filters:
     - "category": Literal["seeds", "fertilizers", "pesticides", "herbicides"]
     - "kind": Literal["paddy", "wheat", "maize", "cotton", "mustard", "vegetable"]
     - "brand": string (e.g. "Mahadhan", "Syngenta", "Bayer")
     - "season": Literal["kharif", "rabi", "zaid"]
     - "max_price": number
     - "min_price": number
     - "in_stock": boolean

2. "knowledge":
   - Use this to search the agricultural knowledge base (RAG) for crop information, sowing practices, weather impacts, soil types, farming methods, or diseases.
   - You MUST extract a semantic "query" string for the search.

3. "order":
   - Use this to query order status, details, history, or delivery tracking.
   - You MUST extract filters:
     - "status": Literal["delivered", "processing", "pending", "cancelled"]

4. "weather":
   - Use this if the user asks specifically for weather, rain, temperature, humidity, wind, or suitability of farm operations (spraying pesticide, irrigating, sowing seeds, applying fertilizer, harvesting).
   - You MUST extract a "query" containing the location name (default to "Punjab" or the farmer's location).

5. "farm_plan":
   - Use this if the user asks to generate a farm plan (e.g., "I want to grow paddy", "create a plan for wheat"), list previous plans, or open/retrieve a specific plan.
   - You MUST extract filters:
     - "action": Literal["create", "list", "retrieve"]
     - "crop": string (e.g. "paddy", "wheat", "maize", "cotton", "mustard")
     - "plan_id": number (optional)

6. "calendar":
   - Use this if the user asks to generate a visual farming crop calendar timeline.
   - You MUST extract filters:
     - "crop": string (e.g. "paddy", "wheat", "maize", "cotton", "mustard")
     - "start_date": string (format YYYY-MM-DD, optional)

Rules:
- You must return a structured plan as JSON matching the schema of PlannerResponse.
- Order of steps should be logical.
- If no tool is needed (e.g. simple greeting like "hello"), return an empty steps list.
- Multi-step planning:
  - If the user asks about crop recommendations or product recommendations (e.g., "Recommend paddy seed"), plan:
    1. "weather" tool (extracting location from profile/query)
    2. "knowledge" tool (with crop details query)
    3. "product" tool (with category/kind filters)
  - If the user asks about farm suitability or sowing times (e.g., "I want to sow wheat tomorrow"), plan:
    1. "weather" tool
    2. "knowledge" tool
"""

def get_clean_schema() -> dict:
    """
    Get the JSON Schema of PlannerResponse and strip all additionalProperties,
    which is not supported by the Gemini Developer API.
    """
    try:
        schema_dict = PlannerResponse.model_json_schema()
    except AttributeError:
        schema_dict = PlannerResponse.schema()

    def remove_additional_properties(item):
        if isinstance(item, dict):
            item.pop("additionalProperties", None)
            for k, v in list(item.items()):
                item[k] = remove_additional_properties(v)
        elif isinstance(item, list):
            item = [remove_additional_properties(x) for x in item]
        return item

    return remove_additional_properties(schema_dict)


def create_plan_fallback(question: str) -> dict:
    """
    Fallback rule-based planner that constructs tool steps locally without Gemini.
    """
    logger.info("Executing Fallback Rule-Based Planner...")
    steps = []
    lower_q = question.lower()
    
    # 1. Check for farm plan indicators
    if any(keyword in lower_q for keyword in ["farm plan", "crop plan", "previous plan", "my plans", "paddy plan", "wheat plan", "grow paddy", "grow wheat", "grow maize", "grow cotton", "grow mustard"]):
        action = "create"
        crop = None
        if any(kw in lower_q for kw in ["show", "list", "previous", "history", "my plans"]):
            action = "list"
        elif any(kw in lower_q for kw in ["open", "retrieve", "show my paddy", "show my wheat"]):
            action = "retrieve"
            
        for c in ["paddy", "wheat", "maize", "cotton", "mustard"]:
            if c in lower_q:
                crop = c
                break
                
        steps.append({
            "tool": "farm_plan",
            "filters": {
                "action": action,
                "crop": crop
            }
        })

    # 1b. Check for calendar timeline indicators
    if any(keyword in lower_q for keyword in ["calendar", "schedule", "timeline", "milestones"]):
        crop = None
        for c in ["paddy", "wheat", "maize", "cotton", "mustard"]:
            if c in lower_q:
                crop = c
                break
        steps.append({
            "tool": "calendar",
            "filters": {
                "crop": crop or "Paddy"
            }
        })
        
    # 2. Weather check conditions
    if not steps and any(keyword in lower_q for keyword in ["weather", "rain", "temperature", "temp", "forecast", "monsoon", "humidity", "wind", "spray", "irrigate", "sow", "fertilizer", "harvest"]):
        loc = "Punjab"
        for place in ["punjab", "ludhiana", "haryana", "delhi", "patiala", "amritsar", "gandhinagar", "ahmedabad"]:
            if place in lower_q:
                loc = place.capitalize()
                break
        steps.append({
            "tool": "weather",
            "query": loc
        })
        
    # 3. Knowledge check conditions
    if not steps and any(keyword in lower_q for keyword in ["how to", "why", "disease", "grow", "sow", "benefit", "info", "help", "care", "recommend"]):
        steps.append({
            "tool": "knowledge",
            "query": question
        })
        
    # 4. Product check conditions
    if not steps and any(keyword in lower_q for keyword in ["seed", "fertilizer", "pesticide", "herbicide", "price", "brand", "product", "buy", "shop", "cost", "recommend"]):
        from app.services.product_tool import extract_filters_rule_based
        p_filters = extract_filters_rule_based(question)
        steps.append({
            "tool": "product",
            "filters": p_filters
        })
        
    # 5. Order check conditions
    if not steps and any(keyword in lower_q for keyword in ["order", "delivery", "track", "shipment", "purchase history", "where is my"]):
        from app.services.order_tool import extract_filters_rule_based
        o_filters = extract_filters_rule_based(question)
        steps.append({
            "tool": "order",
            "filters": o_filters
        })
        
    # Deduplicate steps preserving order
    unique_steps = []
    seen_tools = set()
    for s in steps:
        if s["tool"] not in seen_tools:
            unique_steps.append(s)
            seen_tools.add(s["tool"])
            
    return {"steps": unique_steps}


def create_plan(
    db: Session,
    user_id: int,
    question: str,
    conversation_history: str = ""
) -> dict:
    """
    Builds the context for the planner agent and returns a structured plan.
    Includes caching and a rule-based fallback system.
    """
    # 1. Construct Cache Key
    input_str = f"{question}|||{conversation_history}|||user_{user_id}"
    cache_key = hashlib.md5(input_str.encode("utf-8")).hexdigest()
    
    # 2. Check Cache
    cached_plan = planner_cache.get(cache_key)
    if cached_plan is not None:
        return cached_plan

    # 3. Load preferences to inject into the planner context
    user_profile_summary = build_user_profile_summary(db, user_id)

    prompt_context = f"""
Farmer's Current Question:
{question}

User Profile (Farmer Preferences):
{user_profile_summary}

Conversation History (Recent Context):
{conversation_history}

Please generate the optimal tool execution plan containing pre-extracted filters and queries.
"""

    try:
        from app.services.gemini_service import generate_content_with_retry
        clean_schema = get_clean_schema()
        
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=[
                SYSTEM_PROMPT,
                prompt_context
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=clean_schema,
                temperature=0.0
            )
        )

        text = response.text.strip()
        plan_dict = json.loads(text)
        
        # 4. Set Cache
        planner_cache.set(cache_key, plan_dict, 15 * 60) # 15 minutes
        return plan_dict

    except Exception as e:
        logger.error(f"Planner service error: {e}. Falling back to Rule-Based Planner.")
        fallback_plan = create_plan_fallback(question)
        # Cache the fallback plan too so that we do not hit Gemini on identical subsequent requests
        planner_cache.set(cache_key, fallback_plan, 15 * 60)
        return fallback_plan
