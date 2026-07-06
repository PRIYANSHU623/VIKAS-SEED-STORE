from fastapi import APIRouter

from app.schemas.rag import(
    QueryRequest,
    QueryResponse,
    Source
)

from app.services.rag_service import (
    ask_rag
)

router = APIRouter()

@router.post(
    "/ask",
    response_model=QueryResponse
)
def ask_ai(request: QueryRequest):

    result = ask_rag(
        request.question
    )

    return {

        "answer": result["answer"],

        "sources": [

            Source(text=chunk)

            for chunk in result["sources"]

        ]

    }