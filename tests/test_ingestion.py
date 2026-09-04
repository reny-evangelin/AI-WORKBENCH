import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.ingestion import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_excel,
)

PDF_PATH = "data/documents/refinery_equipment_maintenance_demo.pdf"
DOCX_PATH = "data/documents/refinery_maintenance_demo.docx"
EXCEL_PATH = "data/documents/refinery_maintenance_demo.xlsx"


def test_pdf():
    print("\n--- PDF ---")
    results = extract_text_from_pdf(PDF_PATH)
    print(f"Extracted {len(results)} chunks")
    print(results[0])


def test_docx():
    print("\n--- DOCX ---")
    results = extract_text_from_docx(DOCX_PATH)
    print(f"Extracted {len(results)} chunks")
    print(results[0])


def test_excel():
    print("\n--- EXCEL ---")
    results = extract_text_from_excel(EXCEL_PATH)
    print(f"Extracted {len(results)} chunks")
    print(results[0])


if __name__ == "__main__":
    test_pdf()
    test_docx()
    test_excel()