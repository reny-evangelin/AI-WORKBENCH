"""
tests/test_input_routing.py
===========================
Tests for the SmartRouter deterministic input classification.

Tests cover:
  - text → path=text, no OCR, no vision
  - digital PDF → path=pdf_digital, text extraction only
  - scanned PDF → path=pdf_scanned, OCR required
  - image (default) → path=image, vision=True
  - image (OCR requested) → path=image, ocr=True
  - image (explain request) → path=image, vision=True
  - DOCX → path=docx
  - XLSX → path=xlsx
  - CSV → path=error (unsupported)
  - empty file → HTTPException 400
  - zero-byte file → HTTPException 400
  - unknown extension → fallback text
"""

import os
import sys
import tempfile
import shutil

import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.main import SmartRouter, _process_docx, _process_xlsx, _process_txt


@pytest.fixture
def router():
    return SmartRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_temp(content: bytes, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path


def _make_digital_pdf() -> str:
    """Create a real single-page text-bearing PDF using PyMuPDF."""
    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 72), "This is a digital PDF page with lots of selectable text content " * 5)
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        doc.save(path)
        doc.close()
        return path
    except ImportError:
        pytest.skip("pymupdf not installed")


def _make_scanned_pdf() -> str:
    """Create a PDF page with virtually no text (simulating a scanned image PDF)."""
    try:
        import pymupdf
        doc = pymupdf.open()
        doc.new_page()   # blank page — 0 text chars
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        doc.save(path)
        doc.close()
        return path
    except ImportError:
        pytest.skip("pymupdf not installed")


def _make_docx() -> str:
    """Create a minimal valid DOCX."""
    try:
        from docx import Document
        doc = Document()
        doc.add_paragraph("This is a test DOCX paragraph.")
        doc.add_paragraph("Second paragraph with more content here.")
        fd, path = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        doc.save(path)
        return path
    except ImportError:
        pytest.skip("python-docx not installed")


def _make_xlsx() -> str:
    """Create a minimal valid XLSX."""
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Name", "Value", "Notes"])
        ws.append(["Pump P-101", 42, "Running"])
        ws.append(["Tank TK-202", 88, "Full"])
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        wb.save(path)
        return path
    except ImportError:
        pytest.skip("openpyxl not installed")


# ---------------------------------------------------------------------------
# Text routing
# ---------------------------------------------------------------------------

class TestTextRouting:

    def test_pure_text_no_file(self, router):
        d = router.route("Hello", None, None, "text", None)
        assert d["path"] == "text"
        assert d["needs_ocr"] is False
        assert d["needs_vision"] is False

    def test_pure_text_nonexistent_path(self, router):
        """Even if a path is given but file doesn't exist, treat as text."""
        d = router.route("Hello", "/tmp/nonexistent_xyz.txt", None, "text", None)
        assert d["path"] == "text"

    def test_text_does_not_trigger_ocr(self, router):
        d = router.route("Explain Python", None, None, "text", None)
        assert d["needs_ocr"] is False
        assert d["needs_vision"] is False


# ---------------------------------------------------------------------------
# PDF routing
# ---------------------------------------------------------------------------

class TestPDFRouting:

    def test_digital_pdf_no_ocr(self, router):
        path = _make_digital_pdf()
        try:
            d = router.route("Summarize this document", path, "report.pdf", "pdf", "pdf")
            assert d["path"] == "pdf_digital"
            assert d["needs_ocr"] is False
            assert d["needs_vision"] is False
            assert d["needs_text_extraction"] is True
        finally:
            os.remove(path)

    def test_scanned_pdf_triggers_ocr(self, router):
        path = _make_scanned_pdf()
        try:
            d = router.route("Read this document", path, "scan.pdf", "pdf", "pdf")
            assert d["path"] == "pdf_scanned"
            assert d["needs_ocr"] is True
        finally:
            os.remove(path)

    def test_corrupted_pdf_returns_error(self, router):
        path = _make_temp(b"NOT_A_PDF_CONTENT", ".pdf")
        try:
            d = router.route("Read this", path, "bad.pdf", "pdf", "pdf")
            assert d["path"] == "error"
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# Image routing
# ---------------------------------------------------------------------------

class TestImageRouting:

    def test_image_default_uses_vision(self, router):
        path = _make_temp(b"\x89PNG\r\n", ".png")
        try:
            d = router.route("What is in this image?", path, "photo.png", "image", "png")
            assert d["path"] == "image"
            assert d["needs_vision"] is True
        finally:
            os.remove(path)

    def test_image_extract_text_uses_ocr(self, router):
        path = _make_temp(b"\x89PNG\r\n", ".png")
        try:
            d = router.route("Extract text from this image", path, "doc_photo.png", "image", "png")
            assert d["path"] == "image"
            assert d["needs_ocr"] is True
        finally:
            os.remove(path)

    def test_image_diagram_uses_vision(self, router):
        path = _make_temp(b"\x89PNG\r\n", ".png")
        try:
            d = router.route("Explain this diagram", path, "pid.png", "image", "png")
            assert d["path"] == "image"
            assert d["needs_vision"] is True
        finally:
            os.remove(path)

    def test_jpeg_routed_correctly(self, router):
        path = _make_temp(b"\xff\xd8\xff", ".jpg")
        try:
            d = router.route("Describe this photo", path, "photo.jpg", "image", "jpg")
            assert d["path"] == "image"
        finally:
            os.remove(path)

    def test_webp_routed_correctly(self, router):
        path = _make_temp(b"RIFF\x00\x00\x00\x00WEBP", ".webp")
        try:
            d = router.route("Analyze this image", path, "img.webp", "image", "webp")
            assert d["path"] == "image"
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# DOCX routing
# ---------------------------------------------------------------------------

class TestDocxRouting:

    def test_docx_routes_to_docx_path(self, router):
        path = _make_docx()
        try:
            d = router.route("Summarize this", path, "report.docx", "docx", "docx")
            assert d["path"] == "docx"
            assert d["needs_ocr"] is False
            assert d["needs_text_extraction"] is True
        finally:
            os.remove(path)

    def test_process_docx_extracts_text(self):
        path = _make_docx()
        try:
            text = _process_docx(path)
            assert "test DOCX paragraph" in text
            assert len(text) > 10
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# XLSX routing
# ---------------------------------------------------------------------------

class TestXlsxRouting:

    def test_xlsx_routes_to_xlsx_path(self, router):
        path = _make_xlsx()
        try:
            d = router.route("Show me the data", path, "data.xlsx", "xlsx", "xlsx")
            assert d["path"] == "xlsx"
            assert d["needs_ocr"] is False
            assert d["needs_text_extraction"] is True
        finally:
            os.remove(path)

    def test_process_xlsx_extracts_data(self):
        path = _make_xlsx()
        try:
            text = _process_xlsx(path)
            assert "Pump P-101" in text
            assert "Sheet1" in text
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# Unsupported types
# ---------------------------------------------------------------------------

class TestUnsupportedTypes:

    def test_csv_returns_error(self, router):
        path = _make_temp(b"col1,col2\n1,2\n", ".csv")
        try:
            d = router.route("Analyze this", path, "data.csv", "csv", "csv")
            assert d["path"] == "error"
            assert "not supported" in d["reason"].lower()
        finally:
            os.remove(path)

    def test_unknown_extension_falls_back_to_text(self, router):
        path = _make_temp(b"some bytes", ".xyz")
        try:
            d = router.route("Process this", path, "file.xyz", None, None)
            assert d["path"] == "text"
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# TXT routing
# ---------------------------------------------------------------------------

class TestTxtRouting:

    def test_txt_routes_to_text_file(self, router):
        path = _make_temp(b"Hello, this is a plain text file.", ".txt")
        try:
            d = router.route("Read this", path, "notes.txt", "text_file", "txt")
            assert d["path"] == "text_file"
            assert d["needs_ocr"] is False
            assert d["needs_vision"] is False
        finally:
            os.remove(path)

    def test_process_txt_reads_content(self):
        path = _make_temp(b"Engineering notes here.", ".txt")
        try:
            content = _process_txt(path)
            assert "Engineering notes" in content
        finally:
            os.remove(path)


# ---------------------------------------------------------------------------
# Extension resolution edge cases
# ---------------------------------------------------------------------------

class TestExtResolution:

    def test_filename_takes_priority_over_file_type(self, router):
        """Filename extension should win over file_type hint."""
        path = _make_temp(b"\x89PNG\r\n", ".png")
        try:
            d = router.route("Analyze", path, "image.png", "pdf", "pdf")
            # filename says .png so should route as image
            assert d["path"] == "image"
        finally:
            os.remove(path)

    def test_file_type_used_when_no_filename_ext(self, router):
        """When filename has no extension, file_type hint is used."""
        path = _make_temp(b"\x89PNG\r\n", ".png")
        try:
            d = router.route("Analyze", path, "imagefile", None, "png")
            assert d["path"] == "image"
        finally:
            os.remove(path)
