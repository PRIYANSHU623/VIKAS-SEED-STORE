from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    question: Optional[str] = None
    message: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    response: Optional[str] = None  # Aligned to answer for frontend compatibility
    tool_used: str
    plan: Optional[Dict[str, Any]] = None
    tool_results: Optional[Dict[str, Any]] = None