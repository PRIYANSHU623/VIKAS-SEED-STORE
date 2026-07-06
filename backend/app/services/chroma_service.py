import chromadb

from app.services.embedding_service import generate_embedding

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="knowledge_base"
)


def store_chunk(
    chunk_id: str,
    text: str,
    metadata: dict | None = None,
):
    embedding = generate_embedding(text)

    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata or {}],
    )

    return chunk_id


def search_chunks(
    query_embedding,
    top_k: int = 5,
):
    results =  collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    
    return results


def delete_document_chunks(document_id: int):
    collection.delete(
        where={"document_id": document_id}
    )