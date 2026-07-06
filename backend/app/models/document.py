from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database.db import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    source_type = Column(String, nullable=True, default="Foreign")  # e.g., "ICAR", "KVK", "State Agri University", "Govt Department", "Foreign"
    is_indian = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )