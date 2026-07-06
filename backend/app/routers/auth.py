from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.db import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse

from app.core.security import (
    hash_password, verify_password, create_access_token
)
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    tags=["auth"]
)


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Restrict admin role registration unless bootstrapping the first user
    role = user.role
    if role == "admin":
        any_user = db.query(User).first()
        if any_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot register as admin. Other users already exist."
            )
    else:
        # Force default role to "farmer" to prevent arbitrary roles
        role = "farmer"

    # Create new user
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password_hash=hash_password(user.password),
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """Login user and return access token. Supports both Swagger OAuth2 form data and JSON requests."""
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        email = form_data.get("username")
        password = form_data.get("password")
    else:
        try:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid login request"
            )

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email and password are required"
        )

    db_user = db.query(User).filter(User.email == email).first()

    if not db_user or not verify_password(password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "user_id": db_user.id, "role": db_user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role
        }
    }
