from functools import lru_cache
from rag.embeddings import get_model
from rag.chromadb_store import query_collection
from agent.tracing import traceable

@lru_cache(maxsize=256)
def _embed_query_cached(query: str):
    """Caches embedding generation to avoid repetitive expensive model calls."""
    model = get_model()
    return model.encode(query).tolist()

@lru_cache(maxsize=128)
@traceable(name="RAG_Retrieval")
def retrieve(query, n_results=3):
    """
    Takes a plain text question, embeds it with the same model used for
    documents, and returns the top matching chunks from ChromaDB.
    """
    query_embedding = _embed_query_cached(query)
    results = query_collection(query_embedding, n_results=n_results)
    
    matches = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        matches.append({
            "text": doc,
            "metadata": meta,
            "distance": dist
        })

    return matches