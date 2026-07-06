import os
import shutil
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.document import Document
from app.schemas.knowledge import DocumentResponse
from app.services.rag_service import process_document

router = APIRouter()

@router.post(
    "/upload",
    response_model=DocumentResponse
)
async def upload_document(
    title: str,
    uploaded_by: str,
    source_type: Optional[str] = None,
    is_indian: Optional[bool] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    upload_dir = "app/uploads/knowledge"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Automatic keyword-based inference for Indian agriculture sources
    lower_title = title.lower()
    lower_filename = file.filename.lower()
    
    inferred_is_indian = False
    inferred_source_type = "Foreign"
    
    indian_keywords = [
        "icar", "kvk", "krishi", "vigyan", "pau", "iari", "hau", "pusa", 
        "india", "punjab", "haryana", "state university", "agriculture department",
        "kvks", "icar-iari", "bhandar", "sathi"
    ]
    
    if any(kw in lower_title or kw in lower_filename for kw in indian_keywords):
        inferred_is_indian = True
        if "icar" in lower_title or "icar" in lower_filename:
            inferred_source_type = "ICAR"
        elif "kvk" in lower_title or "kvk" in lower_filename or "vigyan" in lower_title:
            inferred_source_type = "KVK"
        elif "university" in lower_title or "university" in lower_filename or "pau" in lower_title or "hau" in lower_title:
            inferred_source_type = "State Agriculture University"
        elif "department" in lower_title or "department" in lower_filename:
            inferred_source_type = "Government Agriculture Department"
        else:
            inferred_source_type = "ICAR"

    final_is_indian = is_indian if is_indian is not None else inferred_is_indian
    final_source_type = source_type if source_type is not None else inferred_source_type

    # 2. Save Document Record
    document = Document(
        title=title,
        filename=file.filename,
        filepath=file_path,
        uploaded_by=uploaded_by,
        file_type=file.content_type,
        source_type=final_source_type,
        is_indian=final_is_indian
    )

    db.add(document)
    db.commit()
    db.refresh(document)
    
    process_document(
        db=db,
        document_id=document.id,
        pdf_path=file_path
    )

    return document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if os.path.exists(document.filepath):
        os.remove(document.filepath)

    db.delete(document)
    db.commit()

    return {
        "message": "Deleted Successfully"
    }