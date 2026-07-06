from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database.db import get_db
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services.agent_service import run_agent

router = APIRouter(
    prefix="/api",
    tags=["AI Assistant"],
)

@router.post(
    "/chat",
    response_model=ChatResponse,
)
@router.post(
    "/ai/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    fastapi_req: Request,
    db: Session = Depends(get_db),
):
    """
    Unified chat endpoint. Evaluates JWT auth header if present,
    falls back to default user_id=1, and runs the Multi-Tool Agent.
    """
    # 1. Resolve user ID from JWT token or fallback to 1
    user_id = 1
    auth_header = fastapi_req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            from app.core.config import SECRET_KEY, ALGORITHM
            from app.models.user import User
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uid = payload.get("user_id")
            if uid:
                user = db.query(User).filter(User.id == uid).first()
                if user:
                    user_id = user.id
        except Exception as e:
            print(f"Assistant router JWT decode error: {e}")

    # 2. Extract query message
    question = request.question or request.message or ""

    # 3. Execute the Multi-Tool Agent
    result = run_agent(
        db=db,
        user_id=user_id,
        question=question,
        conversation_id=request.conversation_id
    )

    # 4. Map outputs to ChatResponse (populating both answer and response)
    return ChatResponse(
        answer=result["answer"],
        response=result["answer"],
        tool_used=result["tool_used"],
        plan=result["plan"],
        tool_results=result["tool_results"]
    )