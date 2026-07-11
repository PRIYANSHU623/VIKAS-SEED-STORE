import os
import shutil
import time
import uuid
import tempfile
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.product_scanner import run_onboarding_pipeline
from app.services.cloudinary_service import upload_image_to_cloudinary

router = APIRouter()


@router.post("/analyze")
async def analyze_images(
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Onboard product by uploading 1 to 6 images.
    Extracts, validates, enriches details, detects duplicates, and infers agricultural metadata.
    """
    if not images or len(images) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 product image must be uploaded."
        )
    
    if len(images) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 6 product images can be uploaded."
        )

    temp_paths = []
    cloudinary_urls = []

    try:
        for idx, file in enumerate(images):
            # Extract extension safely
            _, ext = os.path.splitext(file.filename or "")
            if not ext:
                ext = ".jpg"
                
            # Create a secure temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name
                
            temp_paths.append(temp_path)

            # Upload to Cloudinary
            cloudinary_url = upload_image_to_cloudinary(temp_path)
            cloudinary_urls.append(cloudinary_url)

        result = run_onboarding_pipeline(temp_paths, cloudinary_urls, db)
        return result
    except Exception as err:
        print(f"Product Onboarding pipeline error: {err}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during onboarding analysis: {str(err)}"
        )
    finally:
        # Delete any temporary local file if one is created
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Error removing temp file {temp_path}: {e}")


    