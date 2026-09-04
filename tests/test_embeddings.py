import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.ingestion import extract_text_from_pdf
from rag.chunker import chunk_documents
from rag.embeddings import embed_chunks

PDF_PATH = "data/documents/refinery_equipment_maintenance_demo.pdf"


def test_embed():
    extracted = extract_text_from_pdf(PDF_PATH)
    chunks = chunk_documents(extracted)
    embedded = embed_chunks(chunks)

    print(f"Embedded {len(embedded)} chunks")
    print("First chunk text:", embedded[0]["text"][:80], "...")
    print("Embedding length:", len(embedded[0]["embedding"]))
    print("First 5 embedding values:", embedded[0]["embedding"][:5])


if __name__ == "__main__":
    test_embed()