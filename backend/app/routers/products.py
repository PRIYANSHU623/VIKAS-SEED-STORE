import base64
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

from app.core.dependencies import (
    get_current_user,
    get_current_admin
)

def convert_local_image_to_base64(image_url: Optional[str]) -> Optional[str]:
    if not image_url or not image_url.startswith("/uploads/"):
        return image_url
        
    cleaned_path = image_url.lstrip("/")
    
    # Try multiple potential paths to locate the file on disk
    possible_paths = [
        os.path.join("app", cleaned_path),
        cleaned_path,
        os.path.abspath(os.path.join("app", cleaned_path)),
        os.path.abspath(cleaned_path),
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            try:
                _, ext = os.path.splitext(path)
                mime_type = "image/jpeg"
                if ext.lower() == ".png":
                    mime_type = "image/png"
                elif ext.lower() in [".gif", ".webp"]:
                    mime_type = f"image/{ext.lower()[1:]}"
                
                with open(path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    return f"data:{mime_type};base64,{encoded}"
            except Exception as e:
                print(f"Error reading local file {path} for base64 conversion: {e}")
                
    return image_url

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
def get_all_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all products with pagination - Public endpoint"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID - Public endpoint"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Create a new product - Admin only"""
    if product.image_url:
        product.image_url = convert_local_image_to_base64(product.image_url)
        
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update a product - Admin only"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product_update.image_url:
        product_update.image_url = convert_local_image_to_base64(product_update.image_url)
        
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a product - Admin only"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
