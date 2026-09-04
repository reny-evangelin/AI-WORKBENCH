import os

from rag.ingestion import extract_text_from_pdf, extract_text_from_docx, extract_text_from_excel
from rag.chunker import chunk_documents
from rag.embeddings import embed_chunks
from rag.chromadb_store import add_chunks

EXTRACTORS = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".xlsx": extract_text_from_excel,
}


def run_pipeline(documents_dir="data/documents"):
    """
    Processes every supported file in documents_dir:
    extract -> chunk -> embed -> store in ChromaDB.
    Returns a summary dict of what was processed.
    """
    summary = {}

    for filename in os.listdir(documents_dir):
        file_path = os.path.join(documents_dir, filename).replace("\\", "/")
        ext = os.path.splitext(filename)[1].lower()

        extractor = EXTRACTORS.get(ext)
        if extractor is None:
            print(f"Skipping {filename} (unsupported type: {ext})")
            continue

        print(f"Processing {filename} ...")
        extracted = extractor(file_path)
        chunks = chunk_documents(extracted)
        embedded = embed_chunks(chunks)
        ids = add_chunks(embedded)

        summary[filename] = {
            "extracted_items": len(extracted),
            "chunks_stored": len(ids),
        }
        print(f"  -> {len(extracted)} extracted items, {len(ids)} chunks stored")

    return summary


if __name__ == "__main__":
    run_pipeline()