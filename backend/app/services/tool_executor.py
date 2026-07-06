import logging
from sqlalchemy.orm import Session
from app.services.knowledge_tool import run as knowledge_tool
from app.services.product_tool import run as product_tool
from app.services.order_tool import run as order_tool
from app.services.weather_tool import run as weather_tool
from app.services.farm_plan_tool import run as farm_plan_tool
from app.services.crop_calendar_service import generate_crop_calendar

logger = logging.getLogger(__name__)

def execute_plan(
    plan: dict,
    db: Session,
    user_id: int
) -> dict:
    """
    Executes a series of tool steps sequentially. Passes pre-extracted filters
    and queries directly to downstream tools. None of these tools call Gemini.
    """
    merged_results = {}
    steps = plan.get("steps", [])

    for step in steps:
        tool_name = step.get("tool")
        tool_filters = step.get("filters")
        tool_query = step.get("query")
        tool_input = step.get("input") or tool_query or ""

        # Skip if tool name is missing
        if not tool_name:
            continue

        logger.info(f"Executing tool '{tool_name}' with filters={tool_filters}, query='{tool_query}'")

        try:
            if tool_name == "product":
                res = product_tool(question=tool_input, db=db, filters=tool_filters)
                merged_results["product"] = res

            elif tool_name == "knowledge":
                res = knowledge_tool(question=tool_input, query=tool_query)
                merged_results["knowledge"] = res

            elif tool_name == "order":
                res = order_tool(question=tool_input, user_id=user_id, db=db, filters=tool_filters)
                merged_results["order"] = res

            elif tool_name == "weather":
                res = weather_tool(question=tool_input, db=db, user_id=user_id, query=tool_query)
                merged_results["weather"] = res

            elif tool_name == "farm_plan":
                action = tool_filters.get("action", "create") if tool_filters else "create"
                crop = tool_filters.get("crop") if tool_filters else None
                plan_id = tool_filters.get("plan_id") if tool_filters else None
                res = farm_plan_tool(question=tool_input, db=db, user_id=user_id, action=action, crop=crop, plan_id=plan_id)
                merged_results["farm_plan"] = res

            elif tool_name == "calendar":
                crop = tool_filters.get("crop", "Paddy") if tool_filters else "Paddy"
                start_date = tool_filters.get("start_date") if tool_filters else None
                res = generate_crop_calendar(db, user_id, crop, start_date)
                merged_results["calendar"] = {
                    "tool": "calendar",
                    "success": True,
                    "data": res
                }

            elif tool_name == "scanner":
                merged_results["scanner"] = {
                    "tool": "scanner",
                    "success": False,
                    "data": {
                        "message": "Product scanner requires visual image uploads, which is not supported in direct chat conversations."
                    }
                }

            else:
                merged_results[tool_name] = {
                    "tool": tool_name,
                    "success": False,
                    "data": {
                        "message": f"Tool '{tool_name}' is not supported or not implemented."
                    }
                }

        except Exception as e:
            logger.error(f"Tool Executor failed for tool '{tool_name}': {e}")
            merged_results[tool_name] = {
                "tool": tool_name,
                "success": False,
                "data": {
                    "message": f"Execution error: {str(e)}"
                }
            }

    return merged_results
