from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.core.dependencies import get_current_user

router = APIRouter()

def seed_mock_testimonials(db: Session):
    """
    Seeds initial testimonials into the database so the homepage doesn't appear empty,
    while removing hardcoding on the frontend.
    """
    mocks = [
        Review(
            user_name="Ramesh Choudhary",
            user_role="Wheat & Paddy Farmer",
            user_location="Karnal, Haryana",
            comment="I bought Basmati Paddy seeds from Vikas Beej Bhandar last season. The germination rate was close to 95%, and the yield was the highest I've had in 5 years. Truly recommend KrishiSathi!",
            rating=5,
            user_image="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150"
        ),
        Review(
            user_name="Baldev Singh",
            user_role="Cotton & Maize Farmer",
            user_location="Bathinda, Punjab",
            comment="The AI assistant helped me identify a leaf pest on my cotton crop in seconds. I purchased the suggested pesticide from this app, and it was delivered within 24 hours. Phenomenal service!",
            rating=5,
            user_image="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=150"
        ),
        Review(
            user_name="Savita Patil",
            user_role="Horticulture Farmer (Grapes)",
            user_location="Nashik, Maharashtra",
            comment="Finding high-quality selective herbicides and NPK fertilizers in one place is hard. KrishiSathi makes it simple. Excellent pricing, fast delivery, and quality guarantee.",
            rating=5,
            user_image="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=150"
        )
    ]
    for m in mocks:
        db.add(m)
    db.commit()

@router.get("/", response_model=List[ReviewResponse])
def get_homepage_reviews(db: Session = Depends(get_db)):
    """Get all homepage testimonials (where product_id is null)"""
    reviews = db.query(Review).filter(Review.product_id == None).all()
    if not reviews:
        seed_mock_testimonials(db)
        reviews = db.query(Review).filter(Review.product_id == None).all()
    return reviews

@router.get("/{product_id}", response_model=List[ReviewResponse])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a specific product, sorted by newest first"""
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()

@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new review - requires authenticated user"""
    # Validation checks
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5."
        )
    if not review.comment or not review.comment.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty."
        )
    
    # Prevent duplicate spam submissions (same user, same product/homepage, same comment)
    spam_check = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.product_id == review.product_id,
        Review.comment == review.comment
    ).first()
    if spam_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted this review."
        )

    db_review = Review(
        product_id=review.product_id,
        user_id=current_user.id,
        user_name=current_user.name,
        rating=review.rating,
        comment=review.comment,
        user_role=review.user_role or (current_user.role.capitalize() if current_user.role else "Farmer"),
        user_location=review.user_location,
        user_image=review.user_image
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit a review - requires owner or admin"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )

    # Permission check: owner or admin
    if db_review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this review."
        )

    if review_update.rating is not None:
        if review_update.rating < 1 or review_update.rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5."
            )
        db_review.rating = review_update.rating

    if review_update.comment is not None:
        if not review_update.comment.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment cannot be empty."
            )
        db_review.comment = review_update.comment

    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a review - requires owner or admin"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )

    # Permission check: owner or admin
    if db_review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this review."
        )

    db.delete(db_review)
    db.commit()
    return {"message": "Review deleted successfully"}
