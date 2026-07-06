import json
from google import genai
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY
from app.models.order import Order

client = genai.Client(
    api_key=GEMINI_API_KEY
)

SYSTEM_PROMPT = """
Extract filters from the user's order question.

Return JSON only.

Fields:

status

Examples:

delivered

processing

pending

cancelled

Example:

{
"status":"delivered"
}
"""

def extract_filters_rule_based(question: str) -> dict:
    """
    Rule-based local keyword matcher to extract order filters without Gemini.
    """
    filters = {}
    lower_q = question.lower()
    for status in ["delivered", "processing", "pending", "cancelled"]:
        if status in lower_q:
            filters["status"] = status
            break
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
            text = text.replace("```json", "")
            text = text.replace("```", "")
        
        return json.loads(text)
    except:
        return {}
    
    
def run(
    question: str,
    user_id: int,
    db: Session,
    filters: dict = None
):
    """
    Order tracking tool. Uses pre-extracted planner filters if available,
    otherwise falls back to rule-based or Gemini-based extraction.
    """
    # 1. Resolve filters
    if filters is None:
        filters = extract_filters_rule_based(question)
        if not filters:
            filters = extract_filters(question)

    query = db.query(Order)

    query = query.filter(
        Order.user_id == user_id
    )

    if filters.get("status"):
        query = query.filter(
            Order.status.ilike(filters["status"])
        )

    orders = query.all()

    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "status": order.status,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "created_at": str(order.created_at)
        })

    return {
        "tool": "order",
        "success": True,
        "data": {
            "filters": filters,
            "count": len(result),
            "orders": result
        }
    }