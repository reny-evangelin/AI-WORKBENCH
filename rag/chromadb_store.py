import uuid
# pyrefly: ignore [missing-import]
import chromadb

_client = None
_collection = None


def get_collection(name="rag_documents", persist_directory="chroma_db"):
    """
    Returns a persistent ChromaDB collection, creating it on first call.
    Data is saved to disk under persist_directory, so it survives between runs.
    """
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(path=persist_directory)
    if _collection is None:
        _collection = _client.get_or_create_collection(name=name)
    return _collection


def add_chunks(chunks):
    """
    Takes the list of chunk dicts (with 'text' and 'embedding' already set
    by embed_chunks) and stores them in ChromaDB.
    """
    collection = get_collection()

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for chunk in chunks:
        ids.append(str(uuid.uuid4()))
        documents.append(chunk["text"])
        embeddings.append(chunk["embedding"])

        metadata = {k: v for k, v in chunk.items() if k not in ("text", "embedding") and v is not None}
        metadatas.append(metadata)

    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return ids


def query_collection(query_embedding, n_results=3):
    """
    Searches the collection for the n_results chunks most similar to query_embedding.
    """
    collection = get_collection()
    return collection.query(query_embeddings=[query_embedding], n_results=n_results)