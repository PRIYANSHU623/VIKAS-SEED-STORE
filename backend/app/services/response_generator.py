import json
import hashlib
import logging
import re
from google import genai
from app.core.config import GEMINI_API_KEY
from app.services.cache_service import response_cache

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are KrishiSathi AI.
You are an intelligent, professional agricultural assistant for Vikas Beej Bhandar.

You MUST answer the farmer using the following structured sections in your markdown response. Do NOT use long paragraphs; keep descriptions short and actionable:

### 🌦️ Weather & Conditions
- Provide current outlook, temperatures, and rain probability.
- If the weather tool returned 'location_required', output exactly: "What is your farm location? Please let me know your city or district so I can check weather suitability for your fields."

### 📖 Knowledge Summary
- Summarize findings from the retrieved knowledge chunks into exactly 3 to 5 clear, bulleted farming advice points.
- Do NOT output raw PDF paragraphs or citation footers verbatim.

### 🌱 Recommended Seeds
- List the recommended seed varieties with brand, price, and fit score.

### 🧪 Recommended Fertilizer
- List recommended fertilizers with brand, price, and fit score.

### 💰 Estimated Cost
- Show the cultivation bundle total cost, average recommendation score, and estimated yield increase percentage.

### 💡 Why These Products
- For the recommended seeds and fertilizers, list their specific traits (maturity time, resistance, soil suitabilities) using short bullet points.

### 🔄 Alternative Options
- Suggest alternative seeds or fertilizers with prices.

### 🌾 Next Farming Advice
- Provide actionable agronomic guidance based on forecast conditions.

Rules:
- Never mention internal technical keywords (JSON, tool, database, API, Chroma).
- Do not output raw PDF excerpts.
- Rank products by match score and present them clearly.
"""

def summarize_chunks_local(chunks: list) -> list:
    """
    Task 3: Local sentence-level summarization of retrieved chunks into 3-5 action points.
    """
    sentences = []
    for chunk in chunks:
        # Split text into sentences
        split_sents = re.split(r'(?<=[.!?])\s+', chunk)
        for s in split_sents:
            s = s.strip()
            # Basic validation
            if len(s) > 20 and s[0].isupper() and not s.startswith("Page") and not s.startswith("http"):
                sentences.append(s)

    unique_sents = []
    seen = set()
    for s in sentences:
        s_lower = s.lower()
        if s_lower not in seen and not any(other in s_lower for other in seen):
            unique_sents.append(s)
            seen.add(s_lower)

    # Filter/prioritize action-oriented guidelines
    action_keywords = ["should", "recommend", "must", "select", "avoid", "apply", "drain", "water", "boost", "prevent", "variety", "sowing", "soil"]
    action_sents = [s for s in unique_sents if any(w in s.lower() for w in action_keywords)]
    
    if len(action_sents) >= 3:
        return action_sents[:5]
        
    return unique_sents[:5] if unique_sents else ["Select certified crop varieties suited for local soil conditions."]


def generate_offline_response(question: str, tool_results: dict) -> str:
    """
    Offline fallback response generator that formats database records, weather,
    and recommendations into the requested 8 sections.
    """
    logger.info("Executing Offline Fallback Response Generator...")
    parts = ["Namaste! I retrieved the following agricultural information from our offline database for you:\n"]
    
    # 1. Weather Section
    parts.append("### 🌦️ Weather & Conditions")
    if "weather" in tool_results:
        w_res = tool_results["weather"]
        if w_res.get("location_required"):
            parts.append("What is your farm location? Please let me know your city or district so I can check weather suitability for your fields.")
        elif w_res.get("success") and w_res.get("data"):
            w = w_res["data"]
            parts.append(f"- **Location**: {w.get('location')}")
            parts.append(f"- **Outlook**: {w.get('forecast')} | **Temp**: {w.get('temperature')}°C | **Humidity**: {w.get('humidity')}%")
            parts.append(f"- **Wind Speed**: {w.get('wind_speed')} km/h | **Rain Probability**: {w.get('rain_probability')}%")
            parts.append(f"- **Farming Advice**: {w.get('recommendation')}")
        else:
            parts.append("Weather details currently unavailable.")
    else:
        parts.append("No weather search executed.")
        
    # 2. Knowledge Summary
    parts.append("\n### 📖 Knowledge Summary")
    if "knowledge" in tool_results:
        k_res = tool_results["knowledge"]
        if k_res.get("success") and k_res.get("data", {}).get("chunks"):
            chunks = k_res["data"]["chunks"]
            bullet_points = summarize_chunks_local(chunks)
            for bp in bullet_points:
                parts.append(f"- {bp}")
        else:
            parts.append("- No agricultural knowledge base documents retrieved for this query.")
    else:
        parts.append("- No agronomic guide check executed.")

    # Extract recommendations and bundles
    recs = []
    bundles = []
    if "recommendation" in tool_results:
        r_res = tool_results["recommendation"]
        if r_res.get("success") and r_res.get("data"):
            recs = r_res["data"].get("recommendations", [])
            bundles = r_res["data"].get("bundles", [])

    # 3. Recommended Seeds
    parts.append("\n### 🌱 Recommended Seeds")
    seeds = [r for r in recs if "seed" in r["category"].lower()]
    if seeds:
        for s in seeds[:3]:
            parts.append(f"- **{s['name']}** ({s['brand']}) - Price: ₹{s['price']} | Match Score: **{s['score']}%** | Confidence: `{s['confidence']}`")
    else:
        parts.append("- No matching seed products recommended.")

    # 4. Recommended Fertilizer
    parts.append("\n### 🧪 Recommended Fertilizer")
    ferts = [r for r in recs if "fertilizer" in r["category"].lower()]
    if ferts:
        for f in ferts[:3]:
            parts.append(f"- **{f['name']}** ({f['brand']}) - Price: ₹{f['price']} | Match Score: **{f['score']}%** | Confidence: `{f['confidence']}`")
    else:
        parts.append("- No matching fertilizer products recommended.")

    # 5. Estimated Cost
    parts.append("\n### 💰 Estimated Cost")
    if bundles:
        for b in bundles:
            parts.append(f"- **{b['bundle_name']}**: Total: **₹{b['estimated_cost']}** | Yield Increase: **{b['yield_benefit']}** | Weather Compatibility: **{b['weather_compatibility']}**")
    else:
        total_p = sum(s["price"] for s in seeds[:1]) + sum(f["price"] for f in ferts[:1])
        if total_p > 0:
            parts.append(f"- Total estimated cost for top items: **₹{total_p:.2f}**")
        else:
            parts.append("- Cost information not applicable.")

    # 6. Why These Products
    parts.append("\n### 💡 Why These Products")
    all_recs = seeds[:2] + ferts[:2]
    if all_recs:
        for p in all_recs:
            parts.append(f"- **{p['name']}**:")
            bullets = p["reason"].split(" • ")
            for b in bullets:
                parts.append(f"  * {b}")
    else:
        parts.append("- No product specifications to display.")

    # 7. Alternative Options
    parts.append("\n### 🔄 Alternative Options")
    alts_found = False
    if bundles:
        for b in bundles:
            alts = b.get("alternatives", {})
            for cat, items in alts.items():
                if items:
                    parts.append(f"- **{cat.capitalize()} alternatives**: " + ", ".join([f"{item['name']} (₹{item['price']})" for item in items]))
                    alts_found = True
    if not alts_found:
        alt_seeds = seeds[3:5]
        alt_ferts = ferts[3:5]
        if alt_seeds:
            parts.append("- **Alternative Seeds**: " + ", ".join([f"{s['name']} (₹{s['price']})" for s in alt_seeds]))
        if alt_ferts:
            parts.append("- **Alternative Fertilizers**: " + ", ".join([f"{f['name']} (₹{f['price']})" for f in alt_ferts]))
        if not alt_seeds and not alt_ferts:
            parts.append("- No alternative crop inputs found in our store inventory.")

    # 8. Next Farming Advice
    parts.append("\n### 🌾 Next Farming Advice")
    if "weather" in tool_results and tool_results["weather"].get("success") and tool_results["weather"]["data"]:
        w = tool_results["weather"]["data"]
        parts.append(f"- Follow current forecast: *{w.get('recommendation')}*")
        parts.append("- Check soil moisture and prepare seedbeds according to local rain forecasts.")
    else:
        parts.append("- Ensure proper soil test checks (pH, NPK levels) before sowing crops.")
        parts.append("- Postpone sowing if heavy rain is expected in your block.")

    # 9. Farm Plan Results (formatting list/retrieve/create actions)
    if "farm_plan" in tool_results:
        f_res = tool_results["farm_plan"]
        if f_res.get("success") and f_res.get("data"):
            data = f_res["data"]
            action = data.get("action")
            
            if action == "list":
                parts.append("\n### 📂 Your Saved Farm Plans:")
                plans = data.get("plans", [])
                if plans:
                    for p in plans:
                        parts.append(f"- **{p['crop']}** ({p['season']}) - Cost: ₹{p['estimated_cost']} | Yield: {p['expected_yield']} | Created: {p['created_at']}")
                else:
                    parts.append("- You have no saved farm plans yet.")
                    
            elif action in ["retrieve", "create"]:
                plan = data.get("plan", {})
                parts.append(f"\n### 🌾 Farm Plan: {plan.get('crop')}")
                parts.append(f"- **Variety**: {plan.get('suitable_variety')} | **Sowing Window**: {plan.get('suitable_season')}")
                parts.append(f"- **Soil Type**: {plan.get('suitable_soil')} | **Water Requirement**: {plan.get('required_water')}")
                
                parts.append("\n**📅 Sowing & Input Schedule:**")
                parts.append("- *Fertilizer Applications*:")
                for fert in plan.get("fertilizer_schedule", []):
                    parts.append(f"  * Day {fert.get('day')}: {fert.get('fertilizer')} ({fert.get('quantity')})")
                parts.append("- *Weed & Pest Control*:")
                for herb in plan.get("herbicide_schedule", []):
                    parts.append(f"  * Day {herb.get('day')}: {herb.get('herbicide')} ({herb.get('quantity')})")
                for pest in plan.get("pesticide_schedule", []):
                    parts.append(f"  * Day {pest.get('day')}: {pest.get('pesticide')} ({pest.get('quantity')})")
                    
                parts.append(f"- **Estimated Cost**: ₹{plan.get('estimated_cost')} | **Expected Yield**: {plan.get('expected_yield')}")
                parts.append(f"- **Harvest Window**: {plan.get('harvest_time')}")

    parts.append("\n*(Note: Showing direct database & calculated agronomic recommendations. Chat response is offline.)*")
    return "\n".join(parts)


def generate_response(
    question: str,
    tool_results: dict,
    conversation_history: str = "",
    user_profile_summary: str = "",
) -> str:
    """
    Synthesize one structured, friendly agricultural response.
    """
    # 1. Check if weather tool reported missing location - short circuit to ask user
    if "weather" in tool_results and tool_results["weather"].get("location_required"):
        return "What is your farm location? Please let me know your city or district so I can check weather suitability for your fields."

    # 2. Construct Cache Key
    results_signature = json.dumps(tool_results, sort_keys=True)
    input_str = f"{question}|||{conversation_history}|||{user_profile_summary}|||{results_signature}"
    cache_key = hashlib.md5(input_str.encode("utf-8")).hexdigest()
    
    # 3. Check Cache
    cached_res = response_cache.get(cache_key)
    if cached_res is not None:
        return cached_res

    prompt = f"""
User Profile (Farmer Preferences):
--------------------
{user_profile_summary}
--------------------

Conversation History:
--------------------
{conversation_history}
--------------------

Merged Tool Results:
--------------------
{json.dumps(tool_results, indent=2)}
--------------------

Farmer's Current Question:
--------------------
{question}
--------------------

Please generate the final response matching the requested sections:
"""
    try:
        from app.services.gemini_service import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model="gemini-2.5-flash",
            contents=[
                SYSTEM_PROMPT,
                prompt
            ]
        )
        final_answer = response.text.strip()
        
        # Set Cache
        response_cache.set(cache_key, final_answer, 10 * 60) # 10 minutes
        return final_answer
        
    except Exception as e:
        logger.error(f"Response generator API failed: {e}. Falling back to offline fallback generator.")
        fallback_res = generate_offline_response(question, tool_results)
        response_cache.set(cache_key, fallback_res, 10 * 60)
        return fallback_res