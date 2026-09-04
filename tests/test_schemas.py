"""
tests/test_schemas.py
=====================
Schema validation test suite for vision/schemas.py (SIH 2026 MVP).

Tests
-----
 1. test_import                  — All public symbols import cleanly.
 2. test_tagged_element_valid    — Valid TaggedElement round-trips correctly.
 3. test_tagged_element_normalise— tag is uppercased/stripped by validator.
 4. test_tagged_element_invalid  — Blank tag raises ValidationError.
 5. test_pid_result_empty        — Minimal/empty PIDAnalysisResult is valid.
 6. test_pid_result_full         — Fully-populated result validates correctly.
 7. test_total_elements          — total_elements is auto-computed.
 8. test_from_parser_dict        — from_parser_dict() builds the model from a parser dict.
 9. test_pid_error_model         — PIDAnalysisError validates correctly.
10. test_real_pipeline_schema    — End-to-end: real image → OCR → PID → Parser → Schema.

Run with:
    .venv\\Scripts\\python.exe -X utf8 tests/test_schemas.py
"""

from __future__ import annotations

import io
import os
import sys

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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_ELEMENT = {
    "tag": "TI-401",
    "confidence": 0.97,
    "original_text": "TAG: TI-401 TEMP INDICATOR",
    "polygon": [[10.0, 20.0], [110.0, 20.0], [110.0, 40.0], [10.0, 40.0]],
}

_FULL_PARSER_DICT = {
    "document_type": "P&ID",
    "equipment":    [],
    "pumps":        [],
    "valves":       [],
    "instruments":  [
        {"tag": "TI-401",  "confidence": 0.97, "original_text": "TAG: TI-401 TEMP INDICATOR", "polygon": []},
        {"tag": "PT-202",  "confidence": 0.98, "original_text": "TAG: PT-202 PRESSURE TRANSMITTER", "polygon": []},
    ],
    "pipes": [
        {"tag": "4-IA-SS-0012-A1A", "confidence": 0.97, "original_text": "LINE NO: 4-IA-SS-0012-A1A", "polygon": []},
    ],
    "raw_text": [
        "P&ID - INSTRUMENT AIR SYSTEM REV-3 SHEET 1 OF 2",
        "TAG: TI-401 TEMP INDICATOR",
        "LINE NO: 4-IA-SS-0012-A1A",
    ],
}

# ---------------------------------------------------------------------------
# Test 1 — import
# ---------------------------------------------------------------------------

def test_import() -> None:
    name = "1. test_import: public symbols importable"
    try:
        from vision.schemas import TaggedElement, PIDAnalysisResult, PIDAnalysisError  # noqa: F401
        record(PASS, name)
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 2 — valid TaggedElement round-trips
# ---------------------------------------------------------------------------

def test_tagged_element_valid() -> None:
    name = "2. test_tagged_element_valid: valid element round-trips"
    try:
        from vision.schemas import TaggedElement
        el = TaggedElement(**_VALID_ELEMENT)
        assert el.tag == "TI-401"
        assert el.confidence == 0.97
        assert el.original_text == "TAG: TI-401 TEMP INDICATOR"
        assert len(el.polygon) == 4
        record(PASS, name, f"tag={el.tag!r} confidence={el.confidence}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 3 — tag normalisation (uppercase + strip)
# ---------------------------------------------------------------------------

def test_tagged_element_normalise() -> None:
    name = "3. test_tagged_element_normalise: tag is uppercased and stripped"
    try:
        from vision.schemas import TaggedElement
        el = TaggedElement(tag=" ti-401 ", confidence=0.9)
        assert el.tag == "TI-401", f"Expected 'TI-401', got {el.tag!r}"
        record(PASS, name, f"Normalised to {el.tag!r}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 4 — blank tag raises ValidationError
# ---------------------------------------------------------------------------

def test_tagged_element_invalid() -> None:
    name = "4. test_tagged_element_invalid: blank tag raises ValidationError"
    try:
        from pydantic import ValidationError
        from vision.schemas import TaggedElement
        try:
            TaggedElement(tag="   ", confidence=0.9)
            record(FAIL, name, "Expected ValidationError but none was raised")
        except ValidationError as exc:
            record(PASS, name, f"ValidationError raised: {exc.error_count()} error(s)")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# Test 5 — empty PIDAnalysisResult is valid
# ---------------------------------------------------------------------------

def test_pid_result_empty() -> None:
    name = "5. test_pid_result_empty: minimal/empty result is valid"
    try:
        from vision.schemas import PIDAnalysisResult
        result = PIDAnalysisResult()
        assert result.document_type == "P&ID"
        assert result.equipment == []
        assert result.instruments == []
        assert result.pipes == []
        assert result.total_elements == 0
        assert result.raw_text == []
        assert result.image_path is None
        record(PASS, name, f"document_type={result.document_type!r} total_elements={result.total_elements}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 6 — fully-populated result
# ---------------------------------------------------------------------------

def test_pid_result_full() -> None:
    name = "6. test_pid_result_full: fully-populated result validates correctly"
    try:
        from vision.schemas import TaggedElement, PIDAnalysisResult
        result = PIDAnalysisResult(
            document_type="P&ID",
            equipment=[TaggedElement(tag="TK-101", confidence=0.95)],
            pumps=[TaggedElement(tag="P-201", confidence=0.93)],
            valves=[TaggedElement(tag="FCV-101", confidence=0.96)],
            instruments=[TaggedElement(tag="TI-401", confidence=0.97),
                         TaggedElement(tag="PT-202", confidence=0.98)],
            pipes=[TaggedElement(tag="4-IA-SS-0012-A1A", confidence=0.97)],
            raw_text=["P&ID SHEET 1 OF 2", "TAG: TI-401"],
            image_path="data/sample_pid/sample.png",
        )
        assert result.total_elements == 6  # 1+1+1+2+1
        # Serialise to dict and check keys
        d = result.model_dump()
        expected_keys = {"document_type", "equipment", "pumps", "valves",
                         "instruments", "pipes", "raw_text", "image_path", "total_elements"}
        missing = expected_keys - d.keys()
        if missing:
            record(FAIL, name, f"Missing keys in model_dump: {missing}")
            return
        record(PASS, name,
               f"total_elements={result.total_elements} keys={sorted(d.keys())}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 7 — total_elements is auto-computed
# ---------------------------------------------------------------------------

def test_total_elements() -> None:
    name = "7. test_total_elements: auto-computed correctly"
    try:
        from vision.schemas import TaggedElement, PIDAnalysisResult
        result = PIDAnalysisResult(
            instruments=[TaggedElement(tag="TI-401"), TaggedElement(tag="PT-202")],
            pipes=[TaggedElement(tag="4-IA-SS-0012-A1A")],
        )
        if result.total_elements == 3:
            record(PASS, name, f"total_elements={result.total_elements}")
        else:
            record(FAIL, name, f"Expected 3, got {result.total_elements}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 8 — from_parser_dict factory
# ---------------------------------------------------------------------------

def test_from_parser_dict() -> None:
    name = "8. test_from_parser_dict: builds model from parser output dict"
    try:
        from vision.schemas import PIDAnalysisResult
        result = PIDAnalysisResult.from_parser_dict(
            _FULL_PARSER_DICT, image_path="data/sample_pid/sample.png"
        )
        assert result.document_type == "P&ID"
        assert len(result.instruments) == 2
        assert len(result.pipes) == 1
        assert len(result.raw_text) == 3
        assert result.total_elements == 3   # 0+0+0+2+1
        assert result.image_path == "data/sample_pid/sample.png"
        instr_tags = [i.tag for i in result.instruments]
        record(PASS, name,
               f"instruments={instr_tags} pipes={[p.tag for p in result.pipes]} "
               f"total={result.total_elements}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 9 — PIDAnalysisError model
# ---------------------------------------------------------------------------

def test_pid_error_model() -> None:
    name = "9. test_pid_error_model: error model validates correctly"
    try:
        from pydantic import ValidationError
        from vision.schemas import PIDAnalysisError

        # Valid error
        err = PIDAnalysisError(
            error="OCR engine failed to initialise",
            image_path="data/sample_pid/diagram.png",
            stage="ocr",
        )
        assert err.error == "OCR engine failed to initialise"
        assert err.stage == "ocr"

        # Minimal (only required field)
        err_min = PIDAnalysisError(error="Unknown failure")
        assert err_min.image_path is None
        assert err_min.stage is None

        # Invalid (empty error string)
        try:
            PIDAnalysisError(error="")
            record(FAIL, name, "Expected ValidationError for empty error string")
            return
        except ValidationError:
            pass  # expected

        record(PASS, name, f"error={err.error!r} stage={err.stage!r}")
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 10 — real end-to-end pipeline through schema
# ---------------------------------------------------------------------------

def test_real_pipeline_schema() -> None:
    name = "10. test_real_pipeline_schema: real image → OCR → PID → Parser → Schema"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, f"Realistic image not found: {REALISTIC_IMAGE}")
        return
    try:
        from vision.ocr    import run_ocr
        from vision.pid    import detect_pid_elements
        from vision.parser import parse_pid_output
        from vision.schemas import PIDAnalysisResult

        ocr_result = run_ocr(REALISTIC_IMAGE)
        if not ocr_result.success:
            if "paddlepaddle" in str(ocr_result.error):
                record(SKIP, name, "paddlepaddle not installed")
                return
            record(FAIL, name, f"OCR failed: {ocr_result.error}")
            return

        pid_data   = detect_pid_elements(ocr_result)
        parsed     = parse_pid_output(ocr_result, pid_data)
        result     = PIDAnalysisResult.from_parser_dict(parsed, image_path=REALISTIC_IMAGE)

        print(f"\n  -- Schema-validated result (real pipeline) --")
        print(f"  document_type  : {result.document_type}")
        print(f"  total_elements : {result.total_elements}")
        print(f"  instruments    : {[i.tag for i in result.instruments]}")
        print(f"  pipes          : {[p.tag for p in result.pipes]}")
        print(f"  raw_text lines : {len(result.raw_text)}")
        print(f"  image_path     : {result.image_path}")
        print(f"\n  JSON preview (first 600 chars):")
        print(f"  {result.model_dump_json(indent=2)[:600]}")

        assert result.document_type == "P&ID"
        assert isinstance(result.total_elements, int)
        assert isinstance(result.raw_text, list)

        record(PASS, name,
               f"document_type={result.document_type!r} "
               f"total_elements={result.total_elements} "
               f"raw_text={len(result.raw_text)} lines")
    except Exception as exc:
        record(FAIL, name, f"Unexpected exception: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("=" * 64)
    print("  vision/schemas.py  --  Test Suite  (SIH 2026 MVP)")
    print("=" * 64)

    test_import()
    test_tagged_element_valid()
    test_tagged_element_normalise()
    test_tagged_element_invalid()
    test_pid_result_empty()
    test_pid_result_full()
    test_total_elements()
    test_from_parser_dict()
    test_pid_error_model()
    test_real_pipeline_schema()

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
