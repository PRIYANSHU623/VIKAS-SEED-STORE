from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='farmer')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")