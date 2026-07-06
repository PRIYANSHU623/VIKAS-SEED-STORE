import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

VISION_PROMPT = """
You are an expert agricultural product onboarding AI assistant.
Analyze the provided images of an agricultural product (up to 6 images, representing front, back, sides, or other panels).
Your goal is to extract every possible field from the visible text.

For each of the following fields, you must return:
1. `value`: The extracted string value, or null if it cannot be found or is highly uncertain. Do not fabricate or guess if not visible.
2. `confidence`: A percentage (integer 0 to 100) representing how confident you are in this extraction. If it is clearly visible, confidence should be 90-100%. If text is blurry, conflicting, or requires inference, lower the confidence. If not visible at all, confidence should be 0.
3. `source`: This must always be "Gemini Vision" initially.

If different images contain conflicting values, choose the most reliable/clearest one and reduce the confidence score appropriately.

Fields to extract:
1. name (Product Name)
2. brand (Brand)
3. manufacturer (Manufacturer)
4. category (Category - must be normalized to one of: "seeds", "fertilizers", "herbicides", "pesticides", or null if undetermined)
5. seed_kind (Seed Kind - e.g., paddy, wheat, maize, mustard, cotton, vegetable, or other crop category, only if seeds category)
6. crop_type (Crop Type - e.g., Rice, Wheat, Tomato, etc.)
7. recommended_season (Recommended Season - e.g., Kharif, Rabi, Zaid, All Seasons)
8. weight (Weight/Volume text, e.g. "10 kg", "1 Litre")
9. net_quantity (Net Quantity, e.g. "1 Unit", "10 kg")
10. mrp (Maximum Retail Price - float or integer value, do not include currency symbols)
11. batch_number (Batch Number)
12. manufacturing_date (Manufacturing Date, e.g. "05/2026")
13. expiry_date (Expiry Date, e.g. "05/2028")
14. registration_number (Registration or approval number)
15. ingredients (Ingredients list, if any)
16. chemical_composition (Chemical Composition, active ingredients percentage, e.g., "Glyphosate 41% SL")
17. usage_instructions (Usage Instructions for the farmer)
18. storage_instructions (Storage instructions)
19. safety_warnings (Safety Warnings or precautions)
20. license_numbers (License Numbers, e.g. Mfg Lic No, Insecticide Lic No)
21. description ( Factual Description based on the packaging)

Return ONLY valid JSON matching this schema:
{
  "name": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "brand": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "manufacturer": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "category": {"value": "seeds | fertilizers | herbicides | pesticides | null", "confidence": 99, "source": "Gemini Vision"},
  "seed_kind": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "crop_type": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "recommended_season": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "weight": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "net_quantity": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "mrp": {"value": 123.45 or null, "confidence": 99, "source": "Gemini Vision"},
  "batch_number": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "manufacturing_date": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "expiry_date": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "registration_number": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "ingredients": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "chemical_composition": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "usage_instructions": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "storage_instructions": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "safety_warnings": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "license_numbers": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"},
  "description": {"value": "string or null", "confidence": 99, "source": "Gemini Vision"}
}

Make sure to parse the MRP field as a float or integer, and keep other fields as strings or null. If any field is completely absent from all images, return null for the value and 0 for confidence.
Do not wrap your response in markdown code blocks or add any extra commentary. Return ONLY the JSON object.
"""

def analyze_images_with_gemini(image_paths: List[str]) -> Dict[str, Any]:
    """
    Uploads the provided image paths to Gemini and prompts the vision model to extract 
    product fields in a structured JSON schema.
    """
    try:
        client = get_client()
        contents = [VISION_PROMPT]
        uploaded_files = []

        for path in image_paths:
            if not os.path.exists(path):
                continue
            uploaded = client.files.upload(file=path)
            uploaded_files.append(uploaded)
            contents.append(uploaded)

        if not uploaded_files:
            raise ValueError("No valid image files provided for analysis.")

        # Request JSON output configuration
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )

        text = response.text.strip()
        # Fallback cleanup just in case markdown is returned
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        result = json.loads(text)
        return result

    except Exception as e:
        print(f"Error in Gemini Vision Service: {e}")
        # Return empty dictionary structure matching schema as fallback
        empty_schema = {}
        fields = [
            "name", "brand", "manufacturer", "category", "seed_kind", "crop_type",
            "recommended_season", "weight", "net_quantity", "mrp", "batch_number",
            "manufacturing_date", "expiry_date", "registration_number", "ingredients",
            "chemical_composition", "usage_instructions", "storage_instructions",
            "safety_warnings", "license_numbers", "description"
        ]
        for field in fields:
            empty_schema[field] = {"value": None, "confidence": 0, "source": "Gemini Vision"}
        return empty_schema
