import logging
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.services.cache_service import planner_cache
from app.services.weather_service import get_weather

logger = logging.getLogger(__name__)

# Default crop stages and offsets (days from start_date / Land Preparation)
CROP_CALENDARS = {
    "paddy": [
        {"stage": "Seed Treatment", "offset": 0, "description": "Treat paddy seeds with fungicide to prevent seed-borne disease."},
        {"stage": "Land Preparation", "offset": 2, "description": "Plough fields, apply compost, and flood soil for puddling."},
        {"stage": "Sowing/Transplanting", "offset": 7, "description": "Sow seeds in nursery or transplant 25-day old seedlings into puddled fields."},
        {"stage": "First Irrigation", "offset": 12, "description": "Maintain shallow water level (2-3 cm) after transplanting."},
        {"stage": "DAP Application", "offset": 20, "description": "Apply basal dosage of DAP (50 kg/acre) to establish root networks."},
        {"stage": "Herbicide Spray", "offset": 35, "description": "Spray pre-emergence herbicide to control weed population early."},
        {"stage": "Urea Application", "offset": 50, "description": "Apply first top-dressing of Urea to boost vegetative tillering."},
        {"stage": "Second Irrigation", "offset": 60, "description": "Maintain soil saturation; irrigate if topsoil dries out."},
        {"stage": "Pesticide Spray", "offset": 70, "description": "Monitor and spray organic neem pesticide for stem borers/planthoppers."},
        {"stage": "Harvest Date", "offset": 120, "description": "Drain fields 10 days prior and harvest paddy when grains turn golden."}
    ],
    "wheat": [
        {"stage": "Seed Treatment", "offset": 0, "description": "Treat wheat seeds with carboxin or thiram for smut control."},
        {"stage": "Land Preparation", "offset": 3, "description": "Deep ploughing to prepare a fine seedbed; apply organic manure."},
        {"stage": "Sowing", "offset": 7, "description": "Drill seeds at a depth of 4-5 cm under optimal soil moisture."},
        {"stage": "First Irrigation", "offset": 21, "description": "Provide first irrigation at Crown Root Initiation (CRI) stage."},
        {"stage": "DAP Application", "offset": 22, "description": "Top dress DAP for crown root development."},
        {"stage": "Herbicide Spray", "offset": 35, "description": "Spray selective herbicide to control broad-leaved weeds."},
        {"stage": "Urea Application", "offset": 45, "description": "Apply urea top-dressing before the second irrigation."},
        {"stage": "Second Irrigation", "offset": 50, "description": "Provide second scheduled irrigation at tillering stage."},
        {"stage": "Pesticide Spray", "offset": 65, "description": "Inspect and spray for rust disease or aphid infestation if observed."},
        {"stage": "Harvest Date", "offset": 110, "description": "Harvest wheat when spikes turn straw-colored and dry."}
    ]
}

def generate_crop_calendar(db: Session, user_id: int, crop: str, start_date_str: Optional[str] = None) -> dict:
    """
    Generates a personalized agronomic calendar including offsets, dates, and warnings.
    Caches calendars for 15 minutes.
    """
    crop_normalized = crop.strip().lower()
    
    # 1. Start Date Resolve
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = datetime.utcnow().date()
    else:
        start_date = datetime.utcnow().date()

    # 2. Check Cache
    cache_key = f"calendar_{user_id}_{crop_normalized}_{start_date.isoformat()}"
    cached_val = planner_cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    # Determine default timeline
    stages = CROP_CALENDARS.get(crop_normalized)
    if not stages:
        # Generate generic crop timeline offsets
        stages = [
            {"stage": "Seed Treatment", "offset": 0, "description": "Treat seeds to prevent diseases."},
            {"stage": "Land Preparation", "offset": 3, "description": "Prepare soil bed."},
            {"stage": "Sowing", "offset": 7, "description": "Sow seeds in the field."},
            {"stage": "First Irrigation", "offset": 15, "description": "Apply first water irrigation."},
            {"stage": "DAP Application", "offset": 20, "description": "Apply DAP fertilizer."},
            {"stage": "Herbicide Spray", "offset": 35, "description": "Control weeds."},
            {"stage": "Urea Application", "offset": 50, "description": "Apply Nitrogen/Urea."},
            {"stage": "Second Irrigation", "offset": 60, "description": "Apply second water irrigation."},
            {"stage": "Pesticide Spray", "offset": 70, "description": "Apply pest control."},
            {"stage": "Harvest Date", "offset": 115, "description": "Harvest mature crop."}
        ]

    # 3. Retrieve Weather Warnings
    weather_warnings = []
    try:
        w_report = get_weather(db, user_id)
        if w_report and not w_report.get("location_required"):
            prob = w_report.get("rain_probability", 0.0)
            if prob > 60:
                weather_warnings.append(
                    f"Warning: {w_report.get('location')} forecast indicates high rain probability ({prob}%). "
                    "Delay sowing or pesticide/herbicide sprays scheduled for today or tomorrow."
                )
            if w_report.get("risks", {}).get("heat_stress") == "High":
                weather_warnings.append("Warning: High heat stress risk today. Irrigate crops in the morning/evening.")
    except Exception:
        pass

    # 4. Map Dates and Status
    today = datetime.utcnow().date()
    mapped_stages = []

    for item in stages:
        event_date = start_date + timedelta(days=item["offset"])
        
        # Status calculation
        if event_date < today:
            status = "completed"
        elif event_date == today:
            status = "current"
        else:
            status = "pending"

        mapped_stages.append({
            "stage": item["stage"],
            "days_offset": item["offset"],
            "scheduled_date": event_date.isoformat(),
            "status": status,
            "description": item["description"]
        })

    response_data = {
        "crop": crop.strip().capitalize(),
        "start_date": start_date.isoformat(),
        "stages": mapped_stages,
        "weather_warnings": weather_warnings
    }

    # 5. Set Cache (15 minutes)
    planner_cache.set(cache_key, response_data, 15 * 60)

    return response_data
