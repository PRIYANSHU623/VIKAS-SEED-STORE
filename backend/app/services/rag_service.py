import uuid
import os
import logging
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.document_chunk import DocumentChunk
from google import genai

from app.services.document_processor import extract_text, chunk_text
from app.services.chroma_service import store_chunk, search_chunks
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def process_document(db: Session, document_id: int, pdf_path: str):
    text = extract_text(pdf_path)
    chunks = chunk_text(text)
    
    for index, chunk in enumerate(chunks):
        embedding_id = str(uuid.uuid4())
        store_chunk(
            chunk_id=embedding_id,
            text=chunk,
            metadata={
                "document_id": document_id,
                "chunk_index": index
            }
        ) 
        
        db_chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            chunk_text=chunk,
            embedding_id=embedding_id
        )
        db.add(db_chunk)
        
    db.commit()
    return len(chunks)


def retrieve_chunks(question: str, top_k: int = 5) -> list:
    """
    Retrieves chunks semantically. Supports Task 5: prioritizes and ranks
    Indian documents (ICAR, KVK, Universities, Govt Departments) higher.
    """
    embedding = generate_embedding(question)

    # 1. Fetch more candidate chunks to enable re-ranking
    results = search_chunks(embedding, top_k * 3)
    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else []

    db = SessionLocal()
    try:
        ranked_chunks = []
        for idx, doc_text in enumerate(documents):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            doc_id = meta.get("document_id")
            
            is_indian = False
            if doc_id:
                from app.models.document import Document
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc and doc.is_indian:
                    is_indian = True

            # Fallback keyword match in chunk content
            if not is_indian:
                lower_text = doc_text.lower()
                indian_keywords = [
                    "icar", "kvk", "krishi", "vigyan", "pau", "iari", "hau", 
                    "pusa", "india", "punjab", "haryana", "bhandar", "sathi"
                ]
                if any(kw in lower_text for kw in indian_keywords):
                    is_indian = True

            ranked_chunks.append({
                "text": doc_text,
                "is_indian": is_indian,
                "boost": 1 if is_indian else 0
            })

        # 2. Sort: Indian chunks first
        ranked_chunks.sort(key=lambda x: x["boost"], reverse=True)
        
        # 3. Slice the requested top_k
        final_chunks = [item["text"] for item in ranked_chunks[:top_k]]
        return final_chunks
    except Exception as e:
        logger.error(f"Error re-ranking RAG search: {e}")
        return documents[:top_k]
    finally:
        db.close()


def ask_rag(question: str):
    chunks = retrieve_chunks(question)
    context = "\n\n".join(chunks)
    
    prompt = f"""
You are KrishiSathi AI, an agricultural expert.

You are given context retrieved from trusted agricultural documents.

Instructions:
1. Answer ONLY using the provided context.
2. If the answer can be reasonably inferred from the context, answer it.
3. Write a helpful, well-structured answer.
4. If the context truly does not contain the answer, say:
   "I couldn't find this information in the uploaded agricultural documents."

Context:
--------------------
{context}
--------------------

Farmer's Question:
{question}

Answer:
"""
    from app.services.gemini_service import generate_content_with_retry
    response = generate_content_with_retry(
        client=client,
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "answer": response.text,
        "sources": chunks
    }