from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class FarmPlan(Base):
    __tablename__ = "farm_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    crop = Column(String, nullable=False)
    season = Column(String, nullable=False)
    plan_json = Column(JSON, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    expected_yield = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
