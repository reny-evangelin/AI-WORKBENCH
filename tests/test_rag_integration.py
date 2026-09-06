import os
import sys
import time

# Suppress noisy warnings
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="opentelemetry")
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")

from rag.embeddings import get_model
from rag.retriever import retrieve
from rag.chromadb_store import get_collection
from rag.pipeline import run_pipeline

def test_rag_integration():
    """Test RAG ingestion, embedding, and retrieval pipeline."""
    # 1. Test Model Load
    model = get_model()
    assert model is not None
    
    # 2. Test Ingestion
    doc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")
    summary = run_pipeline(doc_dir)
    assert isinstance(summary, dict)
    
    # 3. Check ChromaDB State
    collection = get_collection()
    count = collection.count()
    assert count > 0, "Vector store should not be empty after ingestion"
    
    # 4. Test Retrieval
    query = "What is the purpose of a pump in a process plant?"
    results = retrieve(query, n_results=3)
    
    assert len(results) > 0, "Retrieval should return results"
    
    for res in results:
        assert "text" in res
        assert "metadata" in res
        assert "source" in res["metadata"]
