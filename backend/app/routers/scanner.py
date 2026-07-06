import os
import shutil
import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.product_scanner import run_onboarding_pipeline

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

    upload_dir = "app/uploads/products"
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for idx, file in enumerate(images):
        # Extract extension safely
        _, ext = os.path.splitext(file.filename or "")
        if not ext:
            ext = ".jpg"
            
        # Create non-colliding filename
        filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{idx}{ext}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_paths.append(file_path)

    try:
        result = run_onboarding_pipeline(saved_paths, db)
        return result
    except Exception as err:
        print(f"Product Onboarding pipeline error: {err}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during onboarding analysis: {str(err)}"
        )

    