from typing import Dict, Any, List, Tuple

# Important fields that require internet enrichment if missing/unconfident
IMPORTANT_FIELDS = [
    "name",
    "brand",
    "manufacturer",
    "category",
    "crop_type",
    "recommended_season",
    "weight",
    "mrp",
    "description"
]

def validate_extracted_data(data: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """
    Validates extracted product details.
    Returns:
    - warnings: list of string warnings (validation alerts, inconsistencies)
    - needs_enrichment: list of field names that need enrichment (missing or confidence < 80%)
    - validated_data: normalized/validated copy of the input data
    """
    warnings = []
    needs_enrichment = []
    validated_data = {}

    for field, field_info in data.items():
        val = field_info.get("value")
        conf = field_info.get("confidence", 0)
        source = field_info.get("source", "Gemini Vision")

        # Handle null/empty strings
        is_empty = val is None or str(val).strip() == "" or str(val).lower() in ["unknown", "n/a", "none", "not found"]
        
        if is_empty:
            field_info["value"] = None
            field_info["confidence"] = 0
            if field in IMPORTANT_FIELDS:
                needs_enrichment.append(field)
                warnings.append(f"Important field '{field}' is missing.")
        else:
            # Check for low confidence
            if conf < 80:
                if field in IMPORTANT_FIELDS:
                    needs_enrichment.append(field)
                    warnings.append(f"Low confidence ({conf}%) for field '{field}'. Needs verification.")
            
            # Category normalization check
            if field == "category":
                c = str(val).lower().strip()
                valid_categories = ["seeds", "fertilizers", "herbicides", "pesticides"]
                if c not in valid_categories:
                    # try to map
                    if "seed" in c:
                        field_info["value"] = "seeds"
                    elif "fertiliz" in c or "manure" in c:
                        field_info["value"] = "fertilizers"
                    elif "herbicid" in c or "weed" in c:
                        field_info["value"] = "herbicides"
                    elif "pesticid" in c or "insecticid" in c or "fungicid" in c:
                        field_info["value"] = "pesticides"
                    else:
                        warnings.append(f"Invalid category '{val}' detected. Please choose a valid category.")
            
            # Numeric checks
            if field == "mrp":
                try:
                    price_val = float(val)
                    if price_val < 0:
                        warnings.append("MRP price cannot be negative.")
                        field_info["confidence"] = min(field_info["confidence"], 50)
                except ValueError:
                    warnings.append(f"MRP price '{val}' is not a valid number.")
                    field_info["value"] = None
                    field_info["confidence"] = 0
                    if "mrp" not in needs_enrichment:
                        needs_enrichment.append("mrp")

            # Date consistency checks
            if field == "expiry_date":
                mfg_val = data.get("manufacturing_date", {}).get("value")
                if mfg_val and val:
                    # Basic string representation comparison or simple warning
                    # If they contain years, do a quick year check
                    try:
                        import re
                        mfg_years = re.findall(r'\b(20\d{2})\b', str(mfg_val))
                        exp_years = re.findall(r'\b(20\d{2})\b', str(val))
                        if mfg_years and exp_years:
                            m_yr = int(mfg_years[0])
                            e_yr = int(exp_years[0])
                            if e_yr < m_yr:
                                warnings.append(f"Expiry year ({e_yr}) is before manufacturing year ({m_yr}).")
                    except Exception:
                        pass

        validated_data[field] = field_info

    return warnings, needs_enrichment, validated_data
