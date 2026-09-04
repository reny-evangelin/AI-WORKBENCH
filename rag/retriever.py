from rag.embeddings import get_model
from rag.chromadb_store import query_collection


def retrieve(query, n_results=3):
    """
    Takes a plain text question, embeds it with the same model used for
    documents, and returns the top matching chunks from ChromaDB.
    """
    model = get_model()
    query_embedding = model.encode(query).tolist()

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