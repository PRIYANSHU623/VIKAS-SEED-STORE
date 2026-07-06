import os
import json
from typing import Dict, Any, List
from google import genai
from google.genai import types

METADATA_PROMPT = """
You are an agronomy and crop science expert.
We are onboarding a new agricultural product and need to generate professional, high-confidence agricultural metadata, a description, and search tags.

Product Info:
Name: {name}
Brand: {brand}
Category: {category}
Crop Type: {crop_type}
Chemical Composition / Ingredients: {composition}

Please infer and generate the following fields:

1. Agricultural Metadata (Provide values only when confidence is high, otherwise leave empty or null):
   - recommended_soil: e.g. "Loamy", "Alluvial", "Clayey", "Sandy Loam"
   - suitable_region: Geographic regions in India suitable for this crop/product, e.g. "North India", "All India", "Black Soil Region"
   - water_requirement: e.g. "High", "Moderate", "Low", "Irrigated"
   - planting_months: Recommended sowing/planting months, e.g. "June - July", "October - November"
   - harvest_months: Recommended harvesting months, e.g. "September - October", "March - April"
   - target_pest: Major pests controlled or crop pests, e.g. "Stem Borer", "Aphids", "N/A"
   - target_disease: Major diseases controlled or crop diseases, e.g. "Blast", "Rust", "N/A"
   - recommended_dosage: Factual application rate/dosage, e.g. "10 kg per acre", "2 ml per Litre of water"

2. Description:
   - Write a professional, factual, and direct description suitable for farmers and agricultural retailers.
   - Do NOT use marketing buzzwords ("revolutionary", "miracle", "best ever") or invent unproven claims.
   - Focus on crop yields, resistance profile, usage, and key features.
   - Length: 2 to 4 sentences.

3. Search Tags:
   - Generate a list of 5 to 10 relevant, searchable keywords/tags that farmers or admins might search for.
   - Include the brand, crop type, category, season, and features (e.g. ["Hybrid", "High Yield", "Kharif", "Paddy", "Bayer", "Seeds", "Disease Resistant"]).

Return ONLY a valid JSON object matching this schema:
{{
  "recommended_soil": "string or null",
  "suitable_region": "string or null",
  "water_requirement": "string or null",
  "planting_months": "string or null",
  "harvest_months": "string or null",
  "target_pest": "string or null",
  "target_disease": "string or null",
  "recommended_dosage": "string or null",
  "description": "factual description string",
  "tags": ["tag1", "tag2", "tag3"]
}}
Do not write markdown backticks or any commentary. Return ONLY the raw JSON.
"""

def generate_agricultural_metadata(product_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Gemini to generate high-confidence agricultural metadata, descriptions, and tags.
    """
    # Extract details safely
    name = product_details.get("name", {}).get("value", "")
    brand = product_details.get("brand", {}).get("value", "")
    category = product_details.get("category", {}).get("value", "")
    crop_type = product_details.get("crop_type", {}).get("value", "")
    composition = (
        product_details.get("chemical_composition", {}).get("value") or 
        product_details.get("ingredients", {}).get("value") or 
        "Not Specified"
    )

    if not name:
        return {
            "metadata": {},
            "description": product_details.get("description", {}).get("value") or "",
            "tags": []
        }

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "metadata": {},
                "description": product_details.get("description", {}).get("value") or "Factual agricultural product.",
                "tags": []
            }
        client = genai.Client(api_key=api_key)

        prompt = METADATA_PROMPT.format(
            name=name,
            brand=brand,
            category=category,
            crop_type=crop_type,
            composition=composition
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)
        
        # Split into metadata vs description vs tags
        metadata_fields = [
            "recommended_soil", "suitable_region", "water_requirement", 
            "planting_months", "harvest_months", "target_pest", "target_disease", "recommended_dosage"
        ]
        
        metadata = {}
        for field in metadata_fields:
            val = result.get(field)
            if val and str(val).strip() != "" and str(val).lower() not in ["null", "none", "unknown", "n/a"]:
                metadata[field] = val
            else:
                metadata[field] = None

        description = result.get("description") or product_details.get("description", {}).get("value") or "Factual agricultural product."
        tags = result.get("tags") or []

        return {
            "metadata": metadata,
            "description": description,
            "tags": tags
        }

    except Exception as e:
        print(f"Error generating agricultural metadata: {e}")
        return {
            "metadata": {},
            "description": product_details.get("description", {}).get("value") or "Factual agricultural product.",
            "tags": []
        }
