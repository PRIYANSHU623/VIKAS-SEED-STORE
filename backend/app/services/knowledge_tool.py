from app.services.rag_service import retrieve_chunks
from app.services.cache_service import knowledge_cache

def run(question: str, query: str = None):
    """
    Knowledge retrieval tool. Performs semantic search directly on the vector store,
    without calling Gemini. Caches result.
    """
    # 1. Determine query
    search_query = query if query is not None else question

    # 2. Check Cache
    cached_val = knowledge_cache.get(search_query)
    if cached_val is not None:
        return cached_val

    # 3. Retrieve chunks semantic search
    try:
        chunks = retrieve_chunks(search_query)
    except Exception as e:
        print(f"Error retrieving chunks in knowledge tool: {e}")
        chunks = []

    formatted_sources = []
    for index, source in enumerate(chunks, start=1):
        formatted_sources.append({
            "id": index,
            "preview": source[:250] + "..."
            if len(source) > 250
            else source
        })

    # Prepare response dict
    res_dict = {
        "tool": "knowledge",
        "success": True,
        "data": {
            "answer": "Raw documents retrieved.",  # Legacy compatibility
            "sources": formatted_sources,
            "chunks": chunks
        }
    }

    # 4. Set Cache
    knowledge_cache.set(search_query, res_dict, 30 * 60) # 30 minutes

    return res_dict