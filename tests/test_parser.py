"""
tests/test_parser.py
====================
Comprehensive test suite for vision/parser.py (Module 3 — Parser).

Tests
-----
 1. test_import                  — Public symbols import cleanly.
 2. test_empty_ocr_and_pid       — None/empty inputs yield valid empty structure.
 3. test_deduplication           — Duplicate tags are collapsed to one entry.
 4. test_normalization           — Tags are uppercased and stripped.
 5. test_raw_text_dedup          — Duplicate OCR lines are collapsed.
 6. test_failed_ocr_result       — success=False OCR yields empty raw_text but valid dict.
 7. test_synthetic_full          — Realistic synthetic OCR + PID data roundtrip.
 8. test_real_pipeline           — End-to-end: real image → OCR → PID → Parser.

Run with:
    .venv\\Scripts\\python.exe -X utf8 tests/test_parser.py
"""

from __future__ import annotations

import io
import os
import sys

# Force UTF-8 output on Windows.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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


SAMPLE_DIR      = os.path.join(REPO_ROOT, "data", "sample_pid")
REALISTIC_IMAGE = os.path.join(SAMPLE_DIR, "sample_pid_realistic.png")

_EXPECTED_KEYS = {"document_type", "equipment", "pumps", "valves", "instruments", "pipes", "raw_text"}
_EXPECTED_ITEM_KEYS = {"tag", "confidence", "original_text"}


def _check_structure(result: dict, test_name: str) -> bool:
    """Assert the parsed dict has all required keys and correct types."""
    missing_top = _EXPECTED_KEYS - result.keys()
    if missing_top:
        record(FAIL, test_name, f"Missing top-level keys: {missing_top}")
        return False

    if result["document_type"] != "P&ID":
        record(FAIL, test_name, f"document_type is {result['document_type']!r}, expected 'P&ID'")
        return False

    for cat in ("equipment", "pumps", "valves", "instruments", "pipes"):
        if not isinstance(result[cat], list):
            record(FAIL, test_name, f"'{cat}' is not a list")
            return False
        for item in result[cat]:
            missing_item = _EXPECTED_ITEM_KEYS - item.keys()
            if missing_item:
                record(FAIL, test_name, f"Item in '{cat}' missing keys: {missing_item}")
                return False
            if not isinstance(item["tag"], str) or not item["tag"]:
                record(FAIL, test_name, f"Item in '{cat}' has empty/non-str tag")
                return False

    if not isinstance(result["raw_text"], list):
        record(FAIL, test_name, "'raw_text' is not a list")
        return False

    return True


# ---------------------------------------------------------------------------
# Synthetic OCR/PID fixtures
# ---------------------------------------------------------------------------

def _make_ocr_result(texts, *, success=True, error=None):
    """Build a duck-typed OCRResult for unit tests without importing paddleocr."""
    from vision.ocr import OCRResult, OCRLine
    lines = [OCRLine(text=t, confidence=0.95) for t in texts]
    full_text = "\n".join(t for t in texts)
    return OCRResult(image_path="synthetic.png", success=success,
                     lines=lines, full_text=full_text, error=error)


def _make_pid_data(instruments=None, equipment=None, valves=None, pumps=None, pipes=None):
    def _items(tags, cat):
        return [{"tag": t, "confidence": 0.95, "original_text": f"{cat}: {t}", "polygon": []} for t in (tags or [])]
    return {
        "equipment":   _items(equipment, "equipment"),
        "pumps":       _items(pumps, "pumps"),
        "valves":      _items(valves, "valves"),
        "instruments": _items(instruments, "instruments"),
        "pipes":       _items(pipes, "pipes"),
    }


# ---------------------------------------------------------------------------
# Test 1 — import
# ---------------------------------------------------------------------------

def test_import() -> None:
    name = "1. test_import: public symbols importable"
    try:
        from vision.parser import parse_pid_output  # noqa: F401
        record(PASS, name)
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 2 — None/empty inputs
# ---------------------------------------------------------------------------

def test_empty_ocr_and_pid() -> None:
    name = "2. test_empty_ocr_and_pid: None inputs → valid empty structure"
    try:
        from vision.parser import parse_pid_output
        result = parse_pid_output(None, None)
        if _check_structure(result, name):
            empty_cats = all(result[c] == [] for c in ("equipment", "pumps", "valves", "instruments", "pipes"))
            if empty_cats and result["raw_text"] == []:
                record(PASS, name, f"All lists empty as expected")
            else:
                record(FAIL, name, f"Expected all empty lists, got: {result}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 3 — deduplication
# ---------------------------------------------------------------------------

def test_deduplication() -> None:
    name = "3. test_deduplication: duplicate tags collapsed to one entry"
    try:
        from vision.parser import parse_pid_output
        ocr = _make_ocr_result(["TI-401", "PT-202"])
        pid = _make_pid_data(instruments=["TI-401", "TI-401", "PT-202"])
        result = parse_pid_output(ocr, pid)
        if not _check_structure(result, name):
            return
        tags = [i["tag"] for i in result["instruments"]]
        if tags.count("TI-401") == 1 and tags.count("PT-202") == 1:
            record(PASS, name, f"instruments: {tags}")
        else:
            record(FAIL, name, f"Expected deduplication, got: {tags}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 4 — normalisation
# ---------------------------------------------------------------------------

def test_normalization() -> None:
    name = "4. test_normalization: tags are uppercased and stripped"
    try:
        from vision.parser import parse_pid_output
        ocr = _make_ocr_result(["ti-401"])
        pid = {"equipment": [], "pumps": [], "valves": [],
               "pipes": [],
               "instruments": [{"tag": " ti-401 ", "confidence": 0.9,
                                 "original_text": "ti-401", "polygon": []}]}
        result = parse_pid_output(ocr, pid)
        if not _check_structure(result, name):
            return
        tags = [i["tag"] for i in result["instruments"]]
        if tags == ["TI-401"]:
            record(PASS, name, f"Normalised: {tags}")
        else:
            record(FAIL, name, f"Expected ['TI-401'], got {tags}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 5 — raw_text deduplication
# ---------------------------------------------------------------------------

def test_raw_text_dedup() -> None:
    name = "5. test_raw_text_dedup: duplicate OCR lines collapsed"
    try:
        from vision.parser import parse_pid_output
        ocr = _make_ocr_result(["P&ID SHEET 1", "P&ID SHEET 1", "TI-401"])
        result = parse_pid_output(ocr, {})
        if not _check_structure(result, name):
            return
        rt = result["raw_text"]
        if rt.count("P&ID SHEET 1") == 1 and "TI-401" in rt:
            record(PASS, name, f"raw_text: {rt}")
        else:
            record(FAIL, name, f"Unexpected raw_text: {rt}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 6 — failed OCR result
# ---------------------------------------------------------------------------

def test_failed_ocr_result() -> None:
    name = "6. test_failed_ocr_result: success=False → empty raw_text, valid dict"
    try:
        from vision.parser import parse_pid_output
        ocr = _make_ocr_result([], success=False, error="OCR failed for test")
        pid = _make_pid_data(instruments=["TI-401"])
        result = parse_pid_output(ocr, pid)
        if not _check_structure(result, name):
            return
        if result["raw_text"] == [] and result["instruments"] == [{"tag": "TI-401", "confidence": 0.95, "original_text": "instruments: TI-401"}]:
            record(PASS, name, "raw_text empty; instruments preserved from pid_data")
        else:
            record(FAIL, name, f"Unexpected result: raw_text={result['raw_text']}, instr={result['instruments']}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 7 — synthetic full roundtrip
# ---------------------------------------------------------------------------

def test_synthetic_full() -> None:
    name = "7. test_synthetic_full: realistic synthetic data roundtrip"
    try:
        from vision.parser import parse_pid_output
        texts = [
            "P&ID - INSTRUMENT AIR SYSTEM REV-3 SHEET 1 OF 2",
            "TAG: TI-401 TEMP INDICATOR",
            "TAG: PT-202 PRESSURE TRANSMITTER",
            "LINE NO: 4-IA-SS-0012-A1A",
            "TAG: TI-401 TEMP INDICATOR",   # deliberate duplicate
        ]
        ocr = _make_ocr_result(texts)
        pid = _make_pid_data(
            instruments=["TI-401", "PT-202", "TI-401"],  # duplicate instrument
            pipes=["4-IA-SS-0012-A1A"],
        )
        result = parse_pid_output(ocr, pid)
        if not _check_structure(result, name):
            return

        instr_tags = [i["tag"] for i in result["instruments"]]
        pipe_tags  = [i["tag"] for i in result["pipes"]]
        raw_uniq   = len(result["raw_text"]) == len(set(result["raw_text"]))

        ok = (
            instr_tags.count("TI-401") == 1
            and "PT-202" in instr_tags
            and "4-IA-SS-0012-A1A" in pipe_tags
            and raw_uniq
        )
        if ok:
            record(PASS, name,
                   f"instruments={instr_tags} pipes={pipe_tags} raw_text={len(result['raw_text'])} unique lines")
        else:
            record(FAIL, name, f"Unexpected output: {result}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 8 — real pipeline end-to-end
# ---------------------------------------------------------------------------

def test_real_pipeline() -> None:
    name = "8. test_real_pipeline: real image → OCR → PID → Parser"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, f"Realistic image not found: {REALISTIC_IMAGE}")
        return
    try:
        from vision.ocr    import run_ocr
        from vision.pid    import detect_pid_elements
        from vision.parser import parse_pid_output

        ocr_result = run_ocr(REALISTIC_IMAGE)
        if not ocr_result.success:
            if "paddlepaddle" in str(ocr_result.error):
                record(SKIP, name, "paddlepaddle not installed")
                return
            record(FAIL, name, f"OCR failed: {ocr_result.error}")
            return

        pid_data = detect_pid_elements(ocr_result)
        result   = parse_pid_output(ocr_result, pid_data)

        if not _check_structure(result, name):
            return

        print(f"\n  -- Parser output (real pipeline) --")
        for cat in ("equipment", "pumps", "valves", "instruments", "pipes"):
            print(f"  {cat.upper()} ({len(result[cat])}):")
            for item in result[cat]:
                print(f"    {item['tag']}  conf={item['confidence']}  orig={item['original_text']!r}")
        print(f"  RAW TEXT ({len(result['raw_text'])} lines):")
        for t in result["raw_text"]:
            print(f"    {t!r}")

        total = sum(len(result[c]) for c in ("equipment", "pumps", "valves", "instruments", "pipes"))
        record(PASS, name,
               f"document_type={result['document_type']!r}  "
               f"total_elements={total}  raw_text={len(result['raw_text'])} lines")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("=" * 64)
    print("  vision/parser.py  --  Test Suite  (SIH 2026 MVP)")
    print("=" * 64)

    test_import()
    test_empty_ocr_and_pid()
    test_deduplication()
    test_normalization()
    test_raw_text_dedup()
    test_failed_ocr_result()
    test_synthetic_full()
    test_real_pipeline()

    print()
    print("-" * 64)
    passed  = sum(1 for s, _, _ in _results if s == PASS)
    failed  = sum(1 for s, _, _ in _results if s == FAIL)
    skipped = sum(1 for s, _, _ in _results if s == SKIP)
    total   = len(_results)
    print(f"  Results: {passed}/{total} passed | {failed} failed | {skipped} skipped")
    print("-" * 64)
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
