from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.models.farm_plan import FarmPlan
from app.schemas.farm_plan import FarmPlanCreate, FarmPlanResponse
from app.services.farm_planner_service import generate_farm_plan

router = APIRouter(
    prefix="/api/farm-plans",
    tags=["Farm Planner"],
)

def resolve_user_id(request: Request, db: Session = Depends(get_db)) -> int:
    """
    Decodes the JWT bearer token if present to authenticate the user.
    Falls back to default user_id=1.
    """
    user_id = 1
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            from app.core.config import SECRET_KEY, ALGORITHM
            from app.models.user import User
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uid = payload.get("user_id")
            if uid:
                user = db.query(User).filter(User.id == uid).first()
                if user:
                    user_id = user.id
        except Exception:
            pass
    return user_id

@router.post("/generate", response_model=dict)
def generate_plan_endpoint(
    req_body: FarmPlanCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(resolve_user_id)
):
    """
    Generates a crop-specific farming plan, saves it to PostgreSQL, and returns it.
    """
    try:
        plan = generate_farm_plan(db, user_id, req_body.crop)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("", response_model=List[FarmPlanResponse])
def get_user_plans(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(resolve_user_id)
):
    """
    List all previously saved farm plans for the authenticated user.
    """
    plans = db.query(FarmPlan).filter(FarmPlan.user_id == user_id).order_by(FarmPlan.created_at.desc()).all()
    return plans

@router.get("/{plan_id}", response_model=FarmPlanResponse)
def get_plan_details(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(resolve_user_id)
):
    """
    Retrieve specific farm plan details.
    """
    plan = db.query(FarmPlan).filter(FarmPlan.id == plan_id, FarmPlan.user_id == user_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Farm plan not found")
    return plan

from app.services.crop_calendar_service import generate_crop_calendar

@router.get("/calendar", response_model=dict)
def get_calendar_endpoint(
    crop: str,
    start_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(resolve_user_id)
):
    """
    Generates a personalized farming crop calendar.
    """
    try:
        calendar = generate_crop_calendar(db, user_id, crop, start_date)
        return calendar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calendar generation failed: {str(e)}")
