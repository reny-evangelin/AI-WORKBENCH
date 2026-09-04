import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.ingestion import extract_text_from_pdf
from rag.chunker import chunk_documents
from rag.embeddings import embed_chunks
from rag.chromadb_store import add_chunks, query_collection, get_collection

PDF_PATH = "data/documents/refinery_equipment_maintenance_demo.pdf"


def test_store_and_query():
    extracted = extract_text_from_pdf(PDF_PATH)
    chunks = chunk_documents(extracted)
    embedded = embed_chunks(chunks)

    ids = add_chunks(embedded)
    print(f"Stored {len(ids)} chunks in ChromaDB")

    collection = get_collection()
    print("Total items in collection:", collection.count())

    results = query_collection(embedded[0]["embedding"], n_results=2)
    print("\nQuery results:")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print("-", doc[:80], "...", meta)


if __name__ == "__main__":
    test_store_and_query()