from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.db import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    preferred_language = Column(String, default="en")
    preferred_crops = Column(JSON, default=list)  # List of crops, e.g., ["paddy"]
    favourite_brands = Column(JSON, default=list)  # List of brands, e.g., ["Vikas Seeds"]
    budget = Column(Float, nullable=True)
    frequently_purchased_products = Column(JSON, default=list)  # List of products
    farm_location = Column(String, nullable=True)
    soil_type = Column(String, nullable=True)
    weather_location = Column(String, nullable=True)
    preferred_location = Column(String, nullable=True)  # Preferred farm location
    weather_history = Column(JSON, default=list)  # Log of last checked weather metrics
    previous_ai_recommendations = Column(JSON, default=list)
    last_viewed_products = Column(JSON, default=list)

    user = relationship("User", backref="profile")
