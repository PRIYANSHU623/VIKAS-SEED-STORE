from sqlalchemy.orm import Session
from app.services.weather_service import get_weather

def run(question: str, db: Session, user_id: int, query: str = None):
    """
    Executes the weather tool. Receives optional location query from planner,
    calls weather_service, and returns the result. Supports Task 4.
    """
    try:
        report = get_weather(db=db, user_id=user_id, location=query)
        if isinstance(report, dict) and report.get("location_required"):
            return {
                "tool": "weather",
                "success": False,
                "location_required": True,
                "data": report
            }
        return {
            "tool": "weather",
            "success": True,
            "data": report
        }
    except Exception as e:
        return {
            "tool": "weather",
            "success": False,
            "data": {
                "message": f"Failed to retrieve weather: {str(e)}"
            }
        }
