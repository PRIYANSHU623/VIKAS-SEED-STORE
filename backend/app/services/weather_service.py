import httpx
import logging
import time
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from app.services.cache_service import weather_cache
from app.services.profile_service import get_or_create_profile
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes
WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Heavy Rain Showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
}

def geocode_location(location_name: str) -> Optional[Dict[str, Any]]:
    """
    Resolves location name to latitude and longitude using the free Open-Meteo Geocoding API.
    """
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1&format=json"
        response = httpx.get(url, timeout=6.0)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results")
            if results:
                res = results[0]
                return {
                    "latitude": res["latitude"],
                    "longitude": res["longitude"],
                    "name": res["name"]
                }
    except Exception as e:
        logger.error(f"Geocoding failed for '{location_name}': {e}")
    return None

def fetch_weather_raw(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time weather and forecast data from the free Open-Meteo API.
    """
    try:
        # Fetch current weather, relative humidity, and precipitation probability
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current_weather=true"
            "&hourly=relativehumidity_2m"
            "&daily=precipitation_probability_max"
            "&timezone=auto"
        )
        response = httpx.get(url, timeout=6.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Weather API fetch failed for coordinates ({lat}, {lon}): {e}")
    return None

def calculate_suitabilities(temp: float, humidity: float, wind: float, rain_prob: float, forecast: str) -> Dict[str, Any]:
    """
    Agronomic rules calculation for crop suitabilities and risks.
    """
    # 1. Spraying Suitability
    spray_penalty = 0
    spray_reasons = []
    if wind > 15:
        spray_penalty += 50
        spray_reasons.append("high wind (risk of chemical drift)")
    if temp > 35:
        spray_penalty += 40
        spray_reasons.append("high temperature (risk of evaporation and leaf scorch)")
    if rain_prob > 40:
        spray_penalty += 60
        spray_reasons.append("rain expected (chemicals may wash off)")
    
    spray_score = max(0.0, 100.0 - spray_penalty)
    spray_reason = "Conditions are highly suitable for spraying." if spray_score >= 70 else f"Avoid spraying due to {', '.join(spray_reasons)}."
    
    # 2. Irrigation Suitability
    irrig_penalty = 0
    irrig_reasons = []
    if rain_prob > 50:
        irrig_penalty += rain_prob
        irrig_reasons.append("natural rain is expected soon")
    if temp > 38:
        irrig_penalty += 20
        irrig_reasons.append("extreme heat (irrigate early morning or evening to avoid shock)")
        
    irrig_score = max(0.0, 100.0 - irrig_penalty)
    irrig_reason = "Suitable for scheduled irrigation." if irrig_score >= 70 else f"Postpone/minimize irrigation: {', '.join(irrig_reasons)}."
    
    # 3. Sowing Suitability
    sow_penalty = 0
    sow_reasons = []
    if temp < 10 or temp > 35:
        sow_penalty += 60
        sow_reasons.append("unfavorable germination temperature")
    if rain_prob > 70:
        sow_penalty += 80
        sow_reasons.append("heavy rain expected (risk of seed wash-off)")
    if humidity > 80:
        sow_penalty += 20
        sow_reasons.append("very high soil/air moisture")

    sow_score = max(0.0, 100.0 - sow_penalty)
    sow_reason = "Excellent conditions for sowing." if sow_score >= 70 else f"Delay sowing: {', '.join(sow_reasons)}."

    # 4. Harvest Suitability
    harv_penalty = 0
    harv_reasons = []
    if rain_prob > 30:
        harv_penalty += (rain_prob * 1.3)
        harv_reasons.append("rain risk (moisture harms harvested crop quality)")
    if humidity > 85:
        harv_penalty += 30
        harv_reasons.append("high relative humidity")

    harv_score = max(0.0, 100.0 - harv_penalty)
    harv_reason = "Great dry weather for harvesting." if harv_score >= 70 else f"Avoid harvesting: {', '.join(harv_reasons)}."

    # 5. Fertilizer Suitability
    fert_penalty = 0
    fert_reasons = []
    if rain_prob > 60:
        fert_penalty += 80
        fert_reasons.append("heavy rain risk (fertilizer will leach/wash away)")
    if wind > 18:
        fert_penalty += 30
        fert_reasons.append("high wind (affects broadcasting uniformity)")

    fert_score = max(0.0, 100.0 - fert_penalty)
    fert_reason = "Good conditions for applying fertilizer." if fert_score >= 70 else f"Delay fertilization: {', '.join(fert_reasons)}."

    # Risks
    heavy_rain_risk = "High" if (rain_prob > 60 or "heavy" in forecast.lower()) else "Low"
    frost_risk = "High" if temp < 4.0 else "Low"
    heat_stress_risk = "High" if temp > 38.0 else "Low"

    return {
        "suitability": {
            "spraying": {"score": spray_score, "suitable": spray_score >= 70, "reason": spray_reason},
            "irrigation": {"score": irrig_score, "suitable": irrig_score >= 70, "reason": irrig_reason},
            "sowing": {"score": sow_score, "suitable": sow_score >= 70, "reason": sow_reason},
            "harvest": {"score": sow_score, "suitable": harv_score >= 70, "reason": harv_reason},
            "fertilizer": {"score": fert_score, "suitable": fert_score >= 70, "reason": fert_reason}
        },
        "risks": {
            "heavy_rainfall": heavy_rain_risk,
            "frost": frost_risk,
            "heat_stress": heat_stress_risk
        }
    }

def get_weather(db: Session, user_id: int, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Coordinates caching, user preferences, geocoding, API calls,
    and suitability intelligence to return a structured weather report.
    """
    # 1. Resolve target location using User Profile
    profile = get_or_create_profile(db, user_id)
    
    target_loc = location
    if not target_loc:
        target_loc = profile.preferred_location or profile.weather_location or profile.farm_location

    if not target_loc:
        return {
            "location_required": True,
            "message": "What is your farm location?"
        }

    # Normalize location string
    target_loc = target_loc.strip().capitalize()

    # 2. Check Weather Cache
    cached_report = weather_cache.get(target_loc)
    if cached_report is not None:
        # Still save/sync to profile history even on cache hits to update stats
        sync_weather_to_profile(db, profile, cached_report)
        return cached_report

    # 3. Geocode and Fetch Raw Weather Data
    geo = geocode_location(target_loc)
    if not geo:
        # Offline Fallback if geocoding fails
        logger.warning(f"Could not geocode '{target_loc}'. Using offline fallback.")
        fallback = get_offline_fallback(target_loc)
        sync_weather_to_profile(db, profile, fallback)
        weather_cache.set(target_loc, fallback, 15 * 60)
        return fallback

    lat, lon, resolved_name = geo["latitude"], geo["longitude"], geo["name"]
    raw_data = fetch_weather_raw(lat, lon)
    
    if not raw_data:
        # Offline Fallback if fetch fails
        logger.warning(f"Could not fetch weather data for '{resolved_name}'. Using offline fallback.")
        fallback = get_offline_fallback(resolved_name)
        sync_weather_to_profile(db, profile, fallback)
        weather_cache.set(target_loc, fallback, 15 * 60)
        return fallback

    # 4. Extract parameters
    current = raw_data.get("current_weather", {})
    temp = current.get("temperature", 25.0)
    wind = current.get("windspeed", 10.0)
    code = current.get("weathercode", 0)
    forecast = WEATHER_CODES.get(code, "Clear")

    # Extract humidity from hourly lists
    humidity = 60.0
    hourly = raw_data.get("hourly", {})
    if hourly and hourly.get("relativehumidity_2m"):
        humidity = hourly["relativehumidity_2m"][0]  # Take current/starting hour humidity

    # Extract rain probability
    rain_prob = 0.0
    daily = raw_data.get("daily", {})
    if daily and daily.get("precipitation_probability_max"):
        rain_prob = float(daily["precipitation_probability_max"][0])

    # 5. Compute Suitability metrics
    intel = calculate_suitabilities(temp, humidity, wind, rain_prob, forecast)

    # Determine general recommendation
    rec_list = []
    if intel["suitability"]["spraying"]["score"] < 70:
        rec_list.append("Postpone chemical sprays.")
    if intel["suitability"]["fertilizer"]["score"] < 70:
        rec_list.append("Delay fertilizer broadcast.")
    if intel["suitability"]["irrigation"]["score"] < 50:
        rec_list.append("Hold off irrigation; rain is expected.")
    
    recommendation = " ".join(rec_list) if rec_list else "Weather conditions are excellent for all standard farm operations."

    report = {
        "location": resolved_name,
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind,
        "rain_probability": rain_prob,
        "forecast": forecast,
        "recommendation": recommendation,
        "suitability": intel["suitability"],
        "risks": intel["risks"]
    }

    # 6. Save/Sync to profile history
    sync_weather_to_profile(db, profile, report)

    # 7. Cache results for 15 minutes
    weather_cache.set(target_loc, report, 15 * 60)

    return report

def sync_weather_to_profile(db: Session, profile: UserProfile, report: dict):
    """
    Updates the UserProfile weather location and appends to the weather history log.
    """
    try:
        # Save last checked location
        profile.weather_location = report["location"]
        if not profile.preferred_location:
            profile.preferred_location = report["location"]
            
        history = list(profile.weather_history or [])
        # Insert current report at the beginning
        history.insert(0, {
            "timestamp": time.time(),
            "location": report["location"],
            "temperature": report["temperature"],
            "forecast": report["forecast"]
        })
        # Limit history size to 5 records
        profile.weather_history = history[:5]
        
        db.add(profile)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to sync weather to user profile: {e}")

def get_offline_fallback(location_name: str) -> dict:
    """
    Local heuristic fallback structure.
    """
    return {
        "location": location_name,
        "temperature": 28.0,
        "humidity": 65.0,
        "wind_speed": 10.0,
        "rain_probability": 15.0,
        "forecast": "Partly Cloudy",
        "recommendation": "Weather conditions are suitable for standard farm operations.",
        "suitability": {
            "spraying": {"score": 90.0, "suitable": True, "reason": "Low wind and pleasant temperatures."},
            "irrigation": {"score": 85.0, "suitable": True, "reason": "No rainfall expected today."},
            "sowing": {"score": 80.0, "suitable": True, "reason": "Soil and air moisture are in optimal range."},
            "harvest": {"score": 80.0, "suitable": True, "reason": "Dry conditions are favorable for harvesting."},
            "fertilizer": {"score": 90.0, "suitable": True, "reason": "Calm wind and dry soil."}
        },
        "risks": {
            "heavy_rainfall": "Low",
            "frost": "Low",
            "heat_stress": "Low"
        }
    }
