"""
tests/test_final_e2e.py
=======================
Final end-to-end master test for the SIH 2026 MVP vision pipeline.

Runs every test suite and a live API roundtrip via FastAPI TestClient.
No external server process needed — TestClient embeds the ASGI app in-process.

Run with:
    .venv\\Scripts\\python.exe -X utf8 tests/test_final_e2e.py
"""

from __future__ import annotations

import importlib
import io
import json
import os
import struct
import sys
import zlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------------------------------------------------------------------------
# Shared helpers
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

_REQUIRED_JSON_KEYS = {
    "document_type", "equipment", "pumps", "valves",
    "instruments", "pipes", "raw_text", "total_elements", "image_path",
}


def _make_minimal_png() -> bytes:
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig  = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xFF\xFF\xFF"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ---------------------------------------------------------------------------
# Section 1: Module import smoke tests
# ---------------------------------------------------------------------------

def section_imports() -> None:
    print("\n── Section 1: Module Imports ──────────────────────────────────")
    modules = [
        ("vision.ocr",     ["run_ocr", "OCRResult", "OCRLine", "reset_engine"]),
        ("vision.pid",     ["detect_pid_elements"]),
        ("vision.parser",  ["parse_pid_output"]),
        ("vision.schemas", ["TaggedElement", "PIDAnalysisResult", "PIDAnalysisError"]),
        ("vision.api",     ["app"]),
    ]
    for mod_name, symbols in modules:
        try:
            mod = importlib.import_module(mod_name)
            missing = [s for s in symbols if not hasattr(mod, s)]
            if missing:
                record(FAIL, f"import {mod_name}", f"Missing symbols: {missing}")
            else:
                record(PASS, f"import {mod_name}", f"Symbols OK: {symbols}")
        except Exception as exc:
            record(FAIL, f"import {mod_name}", str(exc))


# ---------------------------------------------------------------------------
# Section 2: Schema unit tests (no OCR engine needed)
# ---------------------------------------------------------------------------

def section_schemas() -> None:
    print("\n── Section 2: Pydantic Schema Validation ──────────────────────")

    try:
        from pydantic import ValidationError
        from vision.schemas import TaggedElement, PIDAnalysisResult, PIDAnalysisError

        # 2a — valid element
        el = TaggedElement(tag=" ti-401 ", confidence=0.97, original_text="TAG: TI-401")
        assert el.tag == "TI-401"
        record(PASS, "Schema: TaggedElement valid + normalised", f"tag={el.tag!r}")

        # 2b — blank tag rejected
        try:
            TaggedElement(tag="  ")
            record(FAIL, "Schema: blank tag raises ValidationError", "No error raised")
        except ValidationError:
            record(PASS, "Schema: blank tag raises ValidationError")

        # 2c — empty result
        r = PIDAnalysisResult()
        assert r.total_elements == 0 and r.document_type == "P&ID"
        record(PASS, "Schema: empty PIDAnalysisResult valid", f"total_elements={r.total_elements}")

        # 2d — from_parser_dict factory
        parsed = {
            "document_type": "P&ID",
            "equipment": [], "pumps": [], "valves": [],
            "instruments": [
                {"tag": "TI-401", "confidence": 0.97, "original_text": "TAG: TI-401", "polygon": []},
                {"tag": "PT-202", "confidence": 0.98, "original_text": "TAG: PT-202", "polygon": []},
            ],
            "pipes": [{"tag": "4-IA-SS-0012-A1A", "confidence": 0.97, "original_text": "LINE NO: 4-IA-SS-0012-A1A", "polygon": []}],
            "raw_text": ["P&ID SHEET 1"],
        }
        res = PIDAnalysisResult.from_parser_dict(parsed)
        assert res.total_elements == 3
        record(PASS, "Schema: from_parser_dict factory", f"total_elements={res.total_elements}")

        # 2e — error model
        err = PIDAnalysisError(error="OCR failed", stage="ocr")
        assert err.stage == "ocr"
        record(PASS, "Schema: PIDAnalysisError valid", f"stage={err.stage!r}")

    except Exception as exc:
        record(FAIL, "Schema: unexpected exception", str(exc))


# ---------------------------------------------------------------------------
# Section 3: Parser unit tests (no OCR engine)
# ---------------------------------------------------------------------------

def section_parser() -> None:
    print("\n── Section 3: Parser Unit Tests ───────────────────────────────")
    try:
        from vision.ocr    import OCRResult, OCRLine
        from vision.parser import parse_pid_output

        # 3a — None inputs
        r = parse_pid_output(None, None)
        assert r["document_type"] == "P&ID" and r["instruments"] == []
        record(PASS, "Parser: None inputs → valid empty dict")

        # 3b — deduplication
        ocr = OCRResult("syn.png", True,
                        [OCRLine("TI-401", 0.95), OCRLine("TI-401", 0.95)],
                        "TI-401\nTI-401")
        pid = {"equipment": [], "pumps": [], "valves": [], "pipes": [],
               "instruments": [
                   {"tag": "TI-401", "confidence": 0.95, "original_text": "TI-401", "polygon": []},
                   {"tag": "TI-401", "confidence": 0.95, "original_text": "TI-401", "polygon": []},
               ]}
        r = parse_pid_output(ocr, pid)
        assert len(r["instruments"]) == 1
        record(PASS, "Parser: duplicate tags deduplicated", f"instruments={[i['tag'] for i in r['instruments']]}")

        # 3c — normalisation
        pid2 = {"equipment": [], "pumps": [], "valves": [], "pipes": [],
                "instruments": [{"tag": " ti-401 ", "confidence": 0.9, "original_text": "ti-401", "polygon": []}]}
        r2 = parse_pid_output(ocr, pid2)
        assert r2["instruments"][0]["tag"] == "TI-401"
        record(PASS, "Parser: tag normalised to uppercase", f"tag={r2['instruments'][0]['tag']!r}")

    except Exception as exc:
        record(FAIL, "Parser: unexpected exception", str(exc))


# ---------------------------------------------------------------------------
# Section 4: API tests via TestClient (no running server)
# ---------------------------------------------------------------------------

def section_api() -> None:
    print("\n── Section 4: FastAPI Endpoint Tests (TestClient) ─────────────")
    try:
        from fastapi.testclient import TestClient
        from vision.api import app
        client = TestClient(app, raise_server_exceptions=False)

        # 4a — health
        r = client.get("/health")
        if r.status_code == 200 and r.json() == {"status": "ok"}:
            record(PASS, "API: GET /health → 200", f"body={r.json()}")
        else:
            record(FAIL, "API: GET /health → 200", f"HTTP {r.status_code}")

        # 4b — invalid extension
        r = client.post("/analyze-pid",
                        files={"file": ("bad.txt", b"not image", "text/plain")})
        if r.status_code == 422:
            record(PASS, "API: POST /analyze-pid invalid ext → 422")
        else:
            record(FAIL, "API: POST /analyze-pid invalid ext → 422", f"got {r.status_code}")

        # 4c — invalid MIME
        r = client.post("/analyze-pid",
                        files={"file": ("doc.pdf", b"%PDF", "application/pdf")})
        if r.status_code == 422:
            record(PASS, "API: POST /analyze-pid invalid MIME → 422")
        else:
            record(FAIL, "API: POST /analyze-pid invalid MIME → 422", f"got {r.status_code}")

        # 4d — blank PNG (no crash)
        r = client.post("/analyze-pid",
                        files={"file": ("blank.png", _make_minimal_png(), "image/png")})
        if r.status_code in (200, 422, 500):
            body = r.json()
            if r.status_code == 500 and "error" not in body:
                record(FAIL, "API: POST /analyze-pid blank PNG → no crash", f"Unhandled 500")
            else:
                record(PASS, "API: POST /analyze-pid blank PNG → no crash",
                       f"HTTP {r.status_code}")
        else:
            record(FAIL, "API: POST /analyze-pid blank PNG → no crash", f"HTTP {r.status_code}")

        # 4e — real P&ID image
        if not os.path.exists(REALISTIC_IMAGE):
            record(SKIP, "API: POST /analyze-pid real image", "Sample image not found")
            return

        with open(REALISTIC_IMAGE, "rb") as f:
            img = f.read()

        r = client.post("/analyze-pid",
                        files={"file": ("sample_pid_realistic.png", img, "image/png")})

        if r.status_code == 200:
            body = r.json()
            missing = _REQUIRED_JSON_KEYS - body.keys()
            if missing:
                record(FAIL, "API: POST /analyze-pid real image → 200", f"Missing keys: {missing}")
            else:
                record(PASS, "API: POST /analyze-pid real image → 200",
                       f"document_type={body['document_type']!r}  "
                       f"total_elements={body['total_elements']}  "
                       f"raw_text={len(body['raw_text'])} lines")

            print()
            print("  ── Full API JSON Response ──────────────────────────────")
            print(json.dumps(body, indent=2))
            print()

        elif r.status_code in (422, 500) and "paddlepaddle" in r.text.lower():
            record(SKIP, "API: POST /analyze-pid real image", "paddlepaddle not installed")
        else:
            record(FAIL, "API: POST /analyze-pid real image → 200",
                   f"HTTP {r.status_code}  body={r.text[:200]}")

    except Exception as exc:
        record(FAIL, "API: unexpected exception", f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("=" * 64)
    print("  SIH 2026 MVP — Final End-to-End Test Suite")
    print("  vision: ocr → pid → parser → schemas → api")
    print("=" * 64)

    section_imports()
    section_schemas()
    section_parser()
    section_api()

    # Summary
    print()
    print("=" * 64)
    passed  = sum(1 for s, _, _ in _results if s == PASS)
    failed  = sum(1 for s, _, _ in _results if s == FAIL)
    skipped = sum(1 for s, _, _ in _results if s == SKIP)
    total   = len(_results)
    print(f"  FINAL RESULTS: {passed}/{total} passed | {failed} failed | {skipped} skipped")
    print("=" * 64)
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
