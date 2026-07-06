from sqlalchemy.orm import Session
from app.services.farm_planner_service import generate_farm_plan
from app.models.farm_plan import FarmPlan

def run(question: str, db: Session, user_id: int, action: str = "create", crop: str = None, plan_id: int = None):
    """
    Farm plan execution tool. Handles listing, retrieving, and generating
    farm plans directly within the AI chat execution pipeline.
    """
    try:
        action_clean = (action or "create").lower()
        
        if action_clean == "list":
            plans = db.query(FarmPlan).filter(FarmPlan.user_id == user_id).order_by(FarmPlan.created_at.desc()).all()
            return {
                "tool": "farm_plan",
                "success": True,
                "data": {
                    "action": "list",
                    "plans": [
                        {
                            "id": p.id,
                            "crop": p.crop,
                            "season": p.season,
                            "estimated_cost": p.estimated_cost,
                            "expected_yield": p.expected_yield,
                            "created_at": p.created_at.isoformat()
                        } for p in plans
                    ]
                }
            }

        elif action_clean == "retrieve":
            query = db.query(FarmPlan).filter(FarmPlan.user_id == user_id)
            if plan_id:
                plan = query.filter(FarmPlan.id == plan_id).first()
            elif crop:
                plan = query.filter(FarmPlan.crop == crop.strip().capitalize()).order_by(FarmPlan.created_at.desc()).first()
            else:
                plan = query.order_by(FarmPlan.created_at.desc()).first()
                
            if not plan:
                return {
                    "tool": "farm_plan",
                    "success": False,
                    "data": {"message": f"No farm plan found matching criteria."}
                }
            return {
                "tool": "farm_plan",
                "success": True,
                "data": {
                    "action": "retrieve",
                    "plan": plan.plan_json,
                    "id": plan.id
                }
            }

        else: # "create" / default
            target_crop = crop
            if not target_crop:
                # Try to extract crop from question
                lower_q = question.lower()
                for c in ["paddy", "rice", "wheat", "maize", "cotton", "mustard"]:
                    if c in lower_q:
                        target_crop = "paddy" if c == "rice" else c
                        break
                if not target_crop:
                    target_crop = "Paddy" # fallback
                    
            plan_data = generate_farm_plan(db, user_id, target_crop)
            return {
                "tool": "farm_plan",
                "success": True,
                "data": {
                    "action": "create",
                    "plan": plan_data,
                    "id": plan_data.get("id")
                }
            }
            
    except Exception as e:
        return {
            "tool": "farm_plan",
            "success": False,
            "data": {"message": f"Farm plan operation failed: {str(e)}"}
        }
