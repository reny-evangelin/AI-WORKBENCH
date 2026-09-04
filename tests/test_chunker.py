import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.ingestion import extract_text_from_pdf, extract_text_from_docx, extract_text_from_excel
from rag.chunker import chunk_documents

PDF_PATH = "data/documents/refinery_equipment_maintenance_demo.pdf"
DOCX_PATH = "data/documents/refinery_maintenance_demo.docx"
EXCEL_PATH = "data/documents/refinery_maintenance_demo.xlsx"


def test_chunk_pdf():
    print("\n--- CHUNKED PDF ---")
    extracted = extract_text_from_pdf(PDF_PATH)
    chunks = chunk_documents(extracted)
    print(f"{len(extracted)} extracted items -> {len(chunks)} chunks")
    print(chunks[0])


def test_chunk_docx():
    print("\n--- CHUNKED DOCX ---")
    extracted = extract_text_from_docx(DOCX_PATH)
    chunks = chunk_documents(extracted)
    print(f"{len(extracted)} extracted items -> {len(chunks)} chunks")
    print(chunks[0])


def test_chunk_excel():
    print("\n--- CHUNKED EXCEL ---")
    extracted = extract_text_from_excel(EXCEL_PATH)
    chunks = chunk_documents(extracted)
    print(f"{len(extracted)} extracted items -> {len(chunks)} chunks")
    print(chunks[0])


if __name__ == "__main__":
    test_chunk_pdf()
    test_chunk_docx()
    test_chunk_excel()