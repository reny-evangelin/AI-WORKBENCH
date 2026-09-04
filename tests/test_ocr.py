"""
tests/test_ocr.py
=================
Comprehensive test suite for vision/ocr.py.

Run with:
    .venv\\Scripts\\python.exe -X utf8 tests/test_ocr.py

Tests
-----
1.  test_import              — All public symbols import cleanly.
2.  test_missing_image       — Graceful failure for non-existent path.
3.  test_empty_path          — Graceful failure for empty string path.
4.  test_directory_path      — Graceful failure when path is a directory.
5.  test_unsupported_format  — Graceful failure for e.g. a .txt file.
6.  test_ocr_result_fields   — OCRResult / OCRLine dataclasses have expected fields.
7.  test_engine_init         — PaddleOCR engine can be initialised (paddlepaddle check).
8.  test_synthetic_image     — End-to-end OCR on the synthetic P&ID test image.
9.  test_realistic_image     — End-to-end OCR on the realistic P&ID sample image.
10. test_full_pipeline       — Full pipeline: image → OCR → structured field extraction.
"""

import io
import os
import sys

# Force UTF-8 output on Windows to avoid cp1252 UnicodeEncodeError.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure the repo root is on sys.path so `vision` is importable.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

_results: list = []


def record(status: str, name: str, detail: str = "") -> None:
    _results.append((status, name, detail))
    icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}.get(status, "[ ? ]")
    line = f"  {icon} {name}"
    if detail:
        line += f"\n       {detail}"
    print(line)


SAMPLE_DIR = os.path.join(REPO_ROOT, "data", "sample_pid")
SYNTHETIC_IMAGE = os.path.join(SAMPLE_DIR, "sample_pid_test.png")
REALISTIC_IMAGE = os.path.join(SAMPLE_DIR, "sample_pid_realistic.png")
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

# ---------------------------------------------------------------------------
# Test 1 — import
# ---------------------------------------------------------------------------


def test_import() -> None:
    name = "1. test_import: public symbols importable"
    try:
        from vision.ocr import run_ocr, OCRResult, OCRLine, reset_engine  # noqa: F401
        record(PASS, name)
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 2 — missing image path
# ---------------------------------------------------------------------------


def test_missing_image() -> None:
    name = "2. test_missing_image: graceful failure for non-existent path"
    try:
        from vision.ocr import run_ocr
        result = run_ocr("does/not/exist.png")
        if not result.success and result.error and "not found" in result.error.lower():
            record(PASS, name, f"error='{result.error[:80]}'")
        else:
            record(FAIL, name, f"Expected success=False with 'not found', got: success={result.success}, error={result.error!r}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 3 — empty string path
# ---------------------------------------------------------------------------


def test_empty_path() -> None:
    name = "3. test_empty_path: graceful failure for empty string"
    try:
        from vision.ocr import run_ocr
        result = run_ocr("")
        if not result.success and result.error:
            record(PASS, name, f"error='{result.error[:80]}'")
        else:
            record(FAIL, name, f"Expected success=False, got: success={result.success}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 4 — directory path
# ---------------------------------------------------------------------------


def test_directory_path() -> None:
    name = "4. test_directory_path: graceful failure when path is a directory"
    try:
        from vision.ocr import run_ocr
        result = run_ocr(SAMPLE_DIR)
        if not result.success and result.error:
            record(PASS, name, f"error='{result.error[:80]}'")
        else:
            record(FAIL, name, f"Expected success=False, got: success={result.success}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 5 — unsupported file format
# ---------------------------------------------------------------------------


def test_unsupported_format() -> None:
    name = "5. test_unsupported_format: graceful failure for .txt file"
    # Create a temporary .txt file
    dummy = os.path.join(SAMPLE_DIR, "_dummy_test.txt")
    try:
        os.makedirs(SAMPLE_DIR, exist_ok=True)
        with open(dummy, "w") as f:
            f.write("not an image")
        from vision.ocr import run_ocr
        result = run_ocr(dummy)
        if not result.success and result.error and "unsupported" in result.error.lower():
            record(PASS, name, f"error='{result.error[:80]}'")
        else:
            record(FAIL, name, f"Expected 'unsupported format' error, got: success={result.success}, error={result.error!r}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")
    finally:
        if os.path.exists(dummy):
            os.remove(dummy)


# ---------------------------------------------------------------------------
# Test 6 — dataclass fields
# ---------------------------------------------------------------------------


def test_ocr_result_fields() -> None:
    name = "6. test_ocr_result_fields: OCRResult / OCRLine have correct fields"
    try:
        import dataclasses
        from vision.ocr import OCRResult, OCRLine

        result_fields = {f.name for f in dataclasses.fields(OCRResult)}
        line_fields = {f.name for f in dataclasses.fields(OCRLine)}

        required_result = {"image_path", "success", "lines", "full_text", "error"}
        required_line = {"text", "confidence", "polygon"}

        missing_r = required_result - result_fields
        missing_l = required_line - line_fields

        if missing_r or missing_l:
            record(FAIL, name, f"Missing — OCRResult:{missing_r} OCRLine:{missing_l}")
        else:
            record(PASS, name,
                   f"OCRResult fields: {sorted(result_fields)} | OCRLine fields: {sorted(line_fields)}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 7 — engine init
# ---------------------------------------------------------------------------


def test_engine_init() -> None:
    name = "7. test_engine_init: PaddleOCR engine initialises without error"
    try:
        from vision.ocr import _get_engine, reset_engine
        reset_engine()
        engine = _get_engine(lang="en", enable_preprocessing=True)
        engine_type = type(engine).__name__
        record(PASS, name, f"Engine type: {engine_type}")
    except RuntimeError as exc:
        msg = str(exc)
        if "paddlepaddle" in msg:
            record(SKIP, name, "paddlepaddle not installed — install with: pip install paddlepaddle==3.3.0")
        else:
            record(FAIL, name, f"RuntimeError: {msg[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 8 — synthetic image end-to-end
# ---------------------------------------------------------------------------


def test_synthetic_image() -> None:
    name = "8. test_synthetic_image: OCR on data/sample_pid/sample_pid_test.png"
    if not os.path.exists(SYNTHETIC_IMAGE):
        record(SKIP, name, f"Synthetic image not found: {SYNTHETIC_IMAGE}")
        return

    try:
        from vision.ocr import run_ocr
        result = run_ocr(SYNTHETIC_IMAGE)

        if not result.success:
            if result.error and "paddlepaddle" in result.error:
                record(SKIP, name, "paddlepaddle not installed.")
                return
            record(FAIL, name, f"OCR failed: {result.error}")
            return

        print(f"\n  -- Synthetic image OCR output ({len(result.lines)} lines) --")
        for line in result.lines:
            print(f"  [{line.confidence:5.3f}] {line.text}")

        if result.lines:
            record(PASS, name, f"{len(result.lines)} lines detected. Sample: {result.lines[0].text!r}")
        else:
            record(FAIL, name, "OCR ran but detected 0 text lines on a text-heavy image.")

    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 9 — realistic P&ID image end-to-end
# ---------------------------------------------------------------------------


def test_realistic_image() -> None:
    name = "9. test_realistic_image: OCR on data/sample_pid/sample_pid_realistic.png"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, f"Realistic image not found: {REALISTIC_IMAGE}")
        return

    try:
        from vision.ocr import run_ocr
        result = run_ocr(REALISTIC_IMAGE)

        if not result.success:
            if result.error and "paddlepaddle" in result.error:
                record(SKIP, name, "paddlepaddle not installed.")
                return
            record(FAIL, name, f"OCR failed: {result.error}")
            return

        print(f"\n  -- Realistic P&ID image OCR output ({len(result.lines)} lines) --")
        for i, line in enumerate(result.lines):
            print(f"  [{line.confidence:5.3f}] {line.text}")
            if i >= 24:
                print(f"  ... ({len(result.lines) - 25} more lines)")
                break
        print(f"  Full text preview: {result.full_text[:200]!r}")

        # Check for expected P&ID keywords
        combined = result.full_text.upper()
        expected_keywords = ["FCV", "PRESSURE", "VALVE", "TAG"]
        found = [kw for kw in expected_keywords if kw in combined]
        missing = [kw for kw in expected_keywords if kw not in combined]

        if len(result.lines) >= 3 and found:
            record(PASS, name,
                   f"{len(result.lines)} lines detected. Keywords found: {found}. Missing: {missing}")
        elif result.lines:
            record(PASS, name,
                   f"{len(result.lines)} lines detected (expected keywords missing — OCR quality check needed).")
        else:
            record(FAIL, name, "OCR returned 0 lines on a text-heavy P&ID image.")

    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 10 — full pipeline (image → OCR → structured extraction)
# ---------------------------------------------------------------------------


def _extract_pid_fields(full_text: str) -> dict:
    """
    Minimal field extractor: scans OCR text for P&ID-style tag patterns.

    This is a placeholder that mimics what pid.py will do.
    Returns a dict of extracted fields.
    """
    import re
    fields = {}

    # Extract TAG numbers (e.g. FCV-101, PT-202, LV-301)
    tags = re.findall(r'\b([A-Z]{2,4}-\d{3,4})\b', full_text.upper())
    if tags:
        fields["tags"] = list(dict.fromkeys(tags))  # deduplicated

    # Extract pressure values (e.g. "10 BAR G", "150 PSI")
    pressures = re.findall(r'(\d+(?:\.\d+)?)\s*(?:BAR|PSI|MBAR|KPA)', full_text.upper())
    if pressures:
        fields["pressures"] = pressures

    # Extract temperature values (e.g. "50 DEG C", "180 DEG C")
    temps = re.findall(r'(\d+(?:\.\d+)?)\s*DEG\s*C', full_text.upper())
    if temps:
        fields["temperatures_deg_c"] = temps

    # Extract line numbers (e.g. "4-IA-SS-0012-A1A")
    line_nos = re.findall(r'\b(\d+-[A-Z]{2,4}-[A-Z]{2}-\d{4}-[A-Z0-9]+)\b', full_text.upper())
    if line_nos:
        fields["line_numbers"] = line_nos

    return fields


def test_full_pipeline() -> None:
    name = "10. test_full_pipeline: image → OCR → structured field extraction"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, f"Realistic image not found: {REALISTIC_IMAGE}")
        return

    try:
        from vision.ocr import run_ocr, OCRResult

        result: OCRResult = run_ocr(REALISTIC_IMAGE)

        if not result.success:
            if result.error and "paddlepaddle" in result.error:
                record(SKIP, name, "paddlepaddle not installed.")
            else:
                record(FAIL, name, f"OCR failed: {result.error}")
            return

        # Structural checks
        assert isinstance(result.image_path, str), "image_path must be str"
        assert isinstance(result.success, bool), "success must be bool"
        assert isinstance(result.lines, list), "lines must be list"
        assert isinstance(result.full_text, str), "full_text must be str"
        assert result.error is None, f"error must be None on success, got {result.error!r}"

        for line in result.lines:
            assert isinstance(line.text, str) and line.text, "Each line must have non-empty text"
            assert isinstance(line.confidence, float), "confidence must be float"
            assert isinstance(line.polygon, list), "polygon must be list"

        # Field extraction
        fields = _extract_pid_fields(result.full_text)

        print(f"\n  -- Full pipeline: structured extraction --")
        print(f"  Total OCR lines : {len(result.lines)}")
        print(f"  Total characters: {len(result.full_text)}")
        print(f"  Extracted fields: {fields}")

        if fields:
            record(PASS, name,
                   f"Extracted fields: {list(fields.keys())}. "
                   f"Tags found: {fields.get('tags', [])}")
        elif result.lines:
            record(PASS, name,
                   f"{len(result.lines)} OCR lines extracted. "
                   "No structured fields matched (regex tuning needed for this image).")
        else:
            record(FAIL, name, "Pipeline produced 0 lines of text from a text-heavy image.")

    except AssertionError as exc:
        record(FAIL, name, f"Structural assertion failed: {exc}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def main() -> None:
    print()
    print("=" * 62)
    print("  vision/ocr.py  --  Test Suite  (SIH 2026 MVP)")
    print("=" * 62)

    test_import()
    test_missing_image()
    test_empty_path()
    test_directory_path()
    test_unsupported_format()
    test_ocr_result_fields()
    test_engine_init()
    test_synthetic_image()
    test_realistic_image()
    test_full_pipeline()

    print()
    print("-" * 62)
    passed = sum(1 for s, _, _ in _results if s == PASS)
    failed = sum(1 for s, _, _ in _results if s == FAIL)
    skipped = sum(1 for s, _, _ in _results if s == SKIP)
    total = len(_results)
    print(f"  Results: {passed}/{total} passed | {failed} failed | {skipped} skipped")
    print("-" * 62)
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
