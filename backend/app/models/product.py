from sqlalchemy import Column, Integer, Float, String, JSON
from sqlalchemy.orm import relationship

from app.database.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    category = Column(String)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    image_url = Column(String)
    kind = Column(String, nullable=True)
    season = Column(String, nullable=True)
    
    # New onboarding fields
    manufacturer = Column(String, nullable=True)
    net_quantity = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    mfg_date = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    ingredients = Column(String, nullable=True)
    chemical_composition = Column(String, nullable=True)
    usage_instructions = Column(String, nullable=True)
    storage_instructions = Column(String, nullable=True)
    safety_warnings = Column(String, nullable=True)
    license_numbers = Column(String, nullable=True)
    
    # JSON metadata, confidence scores, sources and tags
    agricultural_metadata = Column(JSON, nullable=True)
    confidence_scores = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")