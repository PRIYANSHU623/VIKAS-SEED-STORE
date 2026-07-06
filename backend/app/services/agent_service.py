import json
import time
import logging
from google import genai
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY
from app.services.knowledge_tool import run as knowledge_tool
from app.services.product_tool import run as product_tool
from app.services.order_tool import run as order_tool

from app.services.planner_service import create_plan
from app.services.tool_executor import execute_plan
from app.services.response_generator import generate_response
from app.services.memory_service import (
    save_message,
    get_recent_messages,
    build_context,
    get_conversation_summary
)
from app.services.profile_service import build_user_profile_summary

logger = logging.getLogger(__name__)
client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are an AI Routing Agent.

Your ONLY task is to decide which tool should answer the user's question.

Available tools:

knowledge
product
order
weather
scanner

Rules:

knowledge
- Farming information
- Crop diseases
- Agriculture
- PDFs
- Crop guide
- Fertilizer usage
- Pesticides

product
- Product search
- Product recommendation
- Price
- Stock
- Brand
- Seed recommendation

order
- Orders
- Delivery
- Tracking
- Purchase history

weather
- Rain
- Temperature
- Weather forecast

scanner
- Product upload
- Product scanner
- Product onboarding

Return ONLY valid JSON.

Example:

{
    "intent":"knowledge"
}
"""


def detect_intent(context: str) -> str:
    """
    Detect which tool should answer the user's query. (Legacy support)
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            SYSTEM_PROMPT,
            context,
        ],
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    try:
        data = json.loads(text)
        return data.get("intent", "knowledge")

    except Exception:
        print("Intent Parsing Failed:")
        print(text)
        return "knowledge"


def execute_tool(
    intent: str,
    question: str,
    context: str = "",
    db=None,
    user_id: int | None = None,
):
    """
    Execute the selected tool. (Legacy support)
    """
    if intent == "knowledge":
        return knowledge_tool(
            question=context if context else question
        )

    elif intent == "product":
        return product_tool(
            question=context if context else question,
            db=db,
        )

    elif intent == "order":
        if user_id is None:
            return {
                "tool": "order",
                "success": False,
                "data": {
                    "message": "User ID is required."
                },
            }

        return order_tool(
            question=context if context else question,
            user_id=user_id,
            db=db,
        )

    elif intent == "weather":
        return {
            "tool": "weather",
            "success": False,
            "data": {
                "message": "Weather tool not implemented."
            },
        }

    elif intent == "scanner":
        return {
            "tool": "scanner",
            "success": False,
            "data": {
                "message": "Scanner tool not implemented."
            },
        }

    return {
        "tool": "unknown",
        "success": False,
        "data": {
            "message": "Unknown intent."
        },
    }


def run_agent(
    db: Session,
    user_id: int,
    question: str,
    conversation_id: str = None
) -> dict:
    """
    True Multi-Tool AI Agent orchestration flow with latencies and max 2 Gemini calls:
    1. Fetch recent conversation history and any long-term summaries.
    2. Save the farmer's question to the database (extracts preferences inline).
    3. Generate a multi-step tool execution plan (Only 1 Gemini call max, or cached).
    4. Execute the plan sequentially and merge the outputs (No Gemini calls).
    5. Generate the final natural response (Only 1 Gemini call max, or cached).
    6. Save KrishiSathi's response to the database with execution metadata.
    7. Return the final payload with metric latencies.
    """
    start_time = time.time()

    # 1. Retrieve history
    recent_msgs = get_recent_messages(db, user_id, limit=10)
    conv_history = build_context(recent_msgs)
    conv_summary = get_conversation_summary(db, user_id)

    full_history = conv_history
    if conv_summary:
        full_history = f"Summary of earlier conversation:\n{conv_summary}\n\n{conv_history}"

    # 2. Save User Message
    save_message(
        db=db,
        user_id=user_id,
        role="user",
        message=question,
        conversation_id=conversation_id
    )

    # 3. Create Plan (Measures Planner Latency)
    planner_start = time.time()
    plan = create_plan(
        db=db,
        user_id=user_id,
        question=question,
        conversation_history=full_history
    )
    planner_latency = time.time() - planner_start
    logger.info(f"[METRIC] Planner Latency: {planner_latency:.4f}s")

    steps = plan.get("steps", [])
    primary_intent = steps[0].get("tool", "knowledge") if steps else "knowledge"
    primary_topic = (steps[0].get("query") or steps[0].get("input") or question) if steps else question

    # 4. Execute planned tools (Measures Tool Latency - No Gemini calls!)
    tool_start = time.time()
    tool_results = execute_plan(
        plan=plan,
        db=db,
        user_id=user_id
    )

    # 4b. Execute Recommendation Engine (No Gemini calls, fully cached/rule-based/agronomic scoring)
    try:
        target_crop = None
        for step in plan.get("steps", []):
            if step.get("tool") == "product" and step.get("filters"):
                target_crop = step["filters"].get("kind")
            elif step.get("tool") == "knowledge" and step.get("query"):
                for crop in ["paddy", "wheat", "maize", "cotton", "mustard"]:
                    if crop in step["query"].lower():
                        target_crop = crop
                        break

        weather_report = tool_results.get("weather", {}).get("data")
        # Implicitly retrieve weather if not run, but relevant to sowing/spraying/recommendations
        if not weather_report and any(kw in question.lower() for kw in ["rain", "weather", "sow", "spray", "irrigate", "fertilizer", "recommend"]):
            from app.services.weather_service import get_weather
            try:
                weather_report = get_weather(db, user_id)
                tool_results["weather"] = {
                    "tool": "weather",
                    "success": True,
                    "data": weather_report
                }
            except Exception as w_err:
                logger.error(f"Implicit weather fetch failed: {w_err}")

        knowledge_chunks = tool_results.get("knowledge", {}).get("data", {}).get("chunks")

        from app.services.recommendation_service import get_recommendations
        recs = get_recommendations(
            db=db,
            user_id=user_id,
            weather_report=weather_report,
            knowledge_chunks=knowledge_chunks,
            target_crop=target_crop
        )
        tool_results["recommendation"] = {
            "tool": "recommendation",
            "success": True,
            "data": recs
        }
    except Exception as rec_err:
        logger.error(f"Recommendation Engine run failed: {rec_err}")

    tool_latency = time.time() - tool_start
    logger.info(f"[METRIC] Tool Latency: {tool_latency:.4f}s")

    # 5. Build user profile summary
    profile_summary = build_user_profile_summary(db, user_id)

    # 6. Generate natural answer (Measures Response Latency)
    response_start = time.time()
    answer = generate_response(
        question=question,
        tool_results=tool_results,
        conversation_history=full_history,
        user_profile_summary=profile_summary
    )
    response_latency = time.time() - response_start
    logger.info(f"[METRIC] Response Latency: {response_latency:.4f}s")

    # 7. Save Assistant Message with tool metadata
    tool_names = list(tool_results.keys())
    tool_used_str = ",".join(tool_names) if tool_names else "none"

    summary_parts = []
    for t_name, t_res in tool_results.items():
        if t_res.get("success"):
            if t_name == "product":
                cnt = t_res.get("data", {}).get("count", 0)
                summary_parts.append(f"product_search_found_{cnt}")
            elif t_name == "knowledge":
                summary_parts.append("knowledge_retrieved")
            elif t_name == "order":
                cnt = t_res.get("data", {}).get("count", 0)
                summary_parts.append(f"order_check_found_{cnt}")
            elif t_name == "weather":
                summary_parts.append("weather_checked")
        else:
            summary_parts.append(f"{t_name}_failed")

    tool_summary = ",".join(summary_parts) if summary_parts else "no_tool"

    save_message(
        db=db,
        user_id=user_id,
        role="assistant",
        message=answer,
        conversation_id=conversation_id,
        tool_used=tool_used_str,
        tool_output_summary=tool_summary,
        intent=primary_intent,
        topic=primary_topic
    )

    total_time = time.time() - start_time
    logger.info(f"[METRIC] Total Request Time: {total_time:.4f}s")

    return {
        "answer": answer,
        "tool_used": tool_used_str,
        "plan": plan,
        "tool_results": tool_results,
        "metrics": {
            "planner_latency": planner_latency,
            "tool_latency": tool_latency,
            "response_latency": response_latency,
            "total_time": total_time
        }
    }