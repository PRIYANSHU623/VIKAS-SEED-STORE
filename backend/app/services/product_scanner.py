import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.gemini_vision_service import analyze_images_with_gemini
from app.services.product_validation_service import validate_extracted_data
from app.services.web_enrichment_service import enrich_missing_fields, search_web_product_images
from app.services.duplicate_detection_service import check_for_duplicate
from app.services.metadata_generation_service import generate_agricultural_metadata

def run_onboarding_pipeline(image_paths: List[str], cloudinary_urls: List[str], db: Session, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
    """
    Coordinates the complete AI Product Onboarding Agent workflow:
    1. Upload images to Cloudinary (handled in router, URLs provided here).
    2. Analyze all images using Gemini Vision.
    3. Extract all visible product information.
    4. Validate extracted information.
    5. Detect missing fields.
    6. Search trusted online sources only when important fields are missing.
    7. Detect duplicate products in PostgreSQL.
    8. Generate agricultural metadata.
    9. Generate product description.
    10. Generate searchable tags.
    11. Return detailed results for review.
    """
    timeline = []
    start_time = time.time()

    def add_step(step_name: str, detail: str = ""):
        elapsed = round(time.time() - start_time, 2)
        timeline.append({
            "step": step_name,
            "detail": detail,
            "timestamp": elapsed,
            "status": "completed"
        })

    # Step 1: Uploading Images to Cloudinary (Completed in Router)
    add_step("Uploading Images", f"Uploaded {len(cloudinary_urls)} image(s) to Cloudinary.")

    # Step 2: Analyzing Images & Step 3: Extracting Info
    print("Pipeline: Running Gemini Vision analysis...")
    raw_extracted = analyze_images_with_gemini(image_paths)
    add_step("Analyzing Images", "Processed images using Gemini Vision.")
    add_step("Extracting Product Information", f"Scanned packaging labels and identified fields.")

    # Step 4: Validating Data & Step 5: Detecting missing fields
    print("Pipeline: Validating extracted data...")
    warnings, needs_enrichment, validated_fields = validate_extracted_data(raw_extracted)
    add_step("Validating Data", f"Completed checks. Found {len(warnings)} issue(s) or missing field(s).")

    # Step 6: Searching Trusted Sources (Web Enrichment)
    product_name = validated_fields.get("name", {}).get("value")
    product_brand = validated_fields.get("brand", {}).get("value")
    product_category = validated_fields.get("category", {}).get("value")
    
    # Fill in fallback names/brands to search if missing
    search_name = product_name or "unknown product"
    search_brand = product_brand or ""
    search_category = product_category or "agriculture"

    enriched_count = 0
    if needs_enrichment and product_name:
        print(f"Pipeline: Searching web for missing fields: {needs_enrichment}...")
        enrichment_results = enrich_missing_fields(
            product_name=search_name,
            brand=search_brand,
            category=search_category,
            missing_fields=needs_enrichment,
            initial_details={f: validated_fields[f] for f in validated_fields}
        )
        
        for field, enriched_info in enrichment_results.items():
            if field in validated_fields and enriched_info.get("value") is not None:
                # Only enrich if we got a high confidence value
                if enriched_info.get("confidence", 0) > 0:
                    validated_fields[field] = {
                        "value": enriched_info.get("value"),
                        "confidence": enriched_info.get("confidence"),
                        "source": enriched_info.get("source", "Web Search")
                    }
                    enriched_count += 1
        
        add_step("Searching Trusted Sources", f"Searched web catalogs. Enriched {enriched_count} field(s).")
    else:
        add_step("Searching Trusted Sources", "Skipped search. No critical fields were missing.")

    # Step 7: Detecting Duplicates
    print("Pipeline: Checking database for duplicates...")
    # Get weight
    weight_val = validated_fields.get("weight", {}).get("value") or validated_fields.get("net_quantity", {}).get("value") or ""
    try:
        duplicate_info = check_for_duplicate(db, search_name, search_brand, str(weight_val))
    except Exception as db_err:
        print(f"Database duplicate check failed (proceeding without check): {db_err}")
        duplicate_info = {"duplicate_found": False, "db_error": True}
    
    if duplicate_info.get("duplicate_found"):
        add_step("Detecting Duplicates", "Duplicate product detected in catalog database.")
    elif duplicate_info.get("db_error"):
        add_step("Detecting Duplicates", "Skipped check. Database is offline/unreachable.")
    else:
        add_step("Detecting Duplicates", "No duplicates found in store database.")

    # Step 8: Generating Agricultural Metadata, Description, Tags (Steps 8, 9, 10)
    print("Pipeline: Generating agricultural metadata and descriptions...")
    meta_tags_desc = generate_agricultural_metadata(validated_fields)
    
    # Update description in fields if generated
    if meta_tags_desc.get("description"):
        validated_fields["description"] = {
            "value": meta_tags_desc.get("description"),
            "confidence": 95,
            "source": "AI Generation"
        }

    # Normalize category/crop_type to keep database CRUD in sync
    category_val = validated_fields.get("category", {}).get("value") or "seeds"
    kind_val = validated_fields.get("seed_kind", {}).get("value") or validated_fields.get("crop_type", {}).get("value") or "other"
    season_val = validated_fields.get("recommended_season", {}).get("value") or "kharif"

    # Save inferred kind/season in agricultural metadata too
    ag_meta = meta_tags_desc.get("metadata") or {}
    ag_meta["category"] = category_val
    ag_meta["seed_kind"] = kind_val
    ag_meta["crop_type"] = kind_val
    ag_meta["recommended_season"] = season_val

    add_step("Generating Metadata", "Inferred soil, season, planting details, factual description, and search tags.")
    
    # Step 11: Preparing Review
    # Search web images
    print("Pipeline: Searching web images...")
    web_images = []
    try:
        web_images = search_web_product_images(search_name, search_brand)
    except Exception as img_err:
        print(f"Failed to fetch web product images: {img_err}")

    add_step("Preparing Review", f"Compiled results, confidence scores, sources and found {len(web_images)} web image(s).")
    add_step("Ready for Approval", "Onboarding agent review pending administrator confirmation.")

    # Return Cloudinary secure URLs directly
    image_urls = cloudinary_urls

    # Calculate overall confidence
    confidences = [info.get("confidence", 0) for info in validated_fields.values() if info.get("confidence") is not None]
    overall_confidence = round(sum(confidences) / len(confidences)) if confidences else 80

    return {
        "fields": validated_fields,
        "agricultural_metadata": ag_meta,
        "warnings": warnings,
        "duplicate_info": duplicate_info,
        "tags": meta_tags_desc.get("tags") or [],
        "image_urls": image_urls,
        "web_image_urls": web_images,
        "timeline": timeline,
        "confidence": overall_confidence
    }
