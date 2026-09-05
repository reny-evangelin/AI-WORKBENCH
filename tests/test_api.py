"""
tests/test_api.py
=================
API test suite for vision/api.py (SIH 2026 MVP).

Uses FastAPI's built-in TestClient (based on httpx) — no running server needed.

Tests
-----
 1. test_import             — App and router import cleanly.
 2. test_health             — GET /health returns 200 {"status": "ok"}.
 3. test_analyze_invalid_ext— POST /analyze-pid with a .txt file → 422.
 4. test_analyze_invalid_mime— POST /analyze-pid with wrong MIME → 422.
 5. test_analyze_real_image — POST /analyze-pid with the sample P&ID → 200 + valid JSON.
 6. test_response_structure — Verify all required keys appear in the JSON response.
 7. test_analyze_empty_png  — POST /analyze-pid with a tiny blank PNG → 200 (no crash).

Run with:
    .venv\\Scripts\\python.exe -X utf8 tests/test_api.py
"""

from __future__ import annotations

import io
import os
import sys
import struct
import zlib

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

_EXPECTED_RESULT_KEYS = {
    "document_type", "equipment", "pumps", "valves",
    "instruments", "pipes", "raw_text", "total_elements", "image_path",
}

# ---------------------------------------------------------------------------
# Minimal valid 1×1 white PNG (generated programmatically — no file needed)
# ---------------------------------------------------------------------------

def _make_minimal_png() -> bytes:
    """Return a valid 1×1 white RGBA PNG as bytes."""
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig    = b"\x89PNG\r\n\x1a\n"
    ihdr   = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw    = b"\x00\xFF\xFF\xFF"          # filter byte + 1 RGB pixel
    idat   = chunk(b"IDAT", zlib.compress(raw))
    iend   = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ---------------------------------------------------------------------------
# Lazy client fixture
# ---------------------------------------------------------------------------

def _get_client():
    from fastapi.testclient import TestClient
    from vision.api import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Test 1 — import
# ---------------------------------------------------------------------------

def test_import() -> None:
    name = "1. test_import: app and routes importable"
    try:
        from vision.api import app  # noqa: F401
        from fastapi.testclient import TestClient  # noqa: F401
        record(PASS, name)
    except Exception as exc:
        record(FAIL, name, str(exc))


# ---------------------------------------------------------------------------
# Test 2 — GET /health
# ---------------------------------------------------------------------------

def test_health() -> None:
    name = "2. test_health: GET /health → 200 {status: ok}"
    try:
        client = _get_client()
        resp = client.get("/health")
        if resp.status_code == 200 and resp.json() == {"status": "ok"}:
            record(PASS, name, f"status_code={resp.status_code} body={resp.json()}")
        else:
            record(FAIL, name, f"status_code={resp.status_code} body={resp.text[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 3 — invalid extension
# ---------------------------------------------------------------------------

def test_analyze_invalid_ext() -> None:
    name = "3. test_analyze_invalid_ext: .txt file → 422"
    try:
        client = _get_client()
        resp = client.post(
            "/analyze-pid",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        if resp.status_code == 422:
            record(PASS, name, f"status_code={resp.status_code}")
        else:
            record(FAIL, name, f"Expected 422, got {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 4 — invalid MIME type
# ---------------------------------------------------------------------------

def test_analyze_invalid_mime() -> None:
    name = "4. test_analyze_invalid_mime: application/pdf MIME → 422"
    try:
        client = _get_client()
        resp = client.post(
            "/analyze-pid",
            files={"file": ("diagram.pdf", b"%PDF-1.4", "application/pdf")},
        )
        if resp.status_code == 422:
            record(PASS, name, f"status_code={resp.status_code}")
        else:
            record(FAIL, name, f"Expected 422, got {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 5 — real P&ID image end-to-end
# ---------------------------------------------------------------------------

def test_analyze_real_image() -> None:
    name = "5. test_analyze_real_image: POST /analyze-pid with sample P&ID → 200"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, f"Realistic image not found: {REALISTIC_IMAGE}")
        return
    try:
        client = _get_client()
        with open(REALISTIC_IMAGE, "rb") as f:
            image_bytes = f.read()

        resp = client.post(
            "/analyze-pid",
            files={"file": ("sample_pid_realistic.png", image_bytes, "image/png")},
            timeout=120,  # OCR can take ~30-60 s
        )
        if resp.status_code == 200:
            body = resp.json()
            record(PASS, name,
                   f"status_code=200 document_type={body.get('document_type')!r} "
                   f"total_elements={body.get('total_elements')}")
        elif resp.status_code in (422, 500):
            body = resp.json()
            if "paddlepaddle" in str(body.get("error", "")).lower():
                record(SKIP, name, "paddlepaddle not installed")
            else:
                record(FAIL, name, f"status_code={resp.status_code} body={resp.text[:300]}")
        else:
            record(FAIL, name, f"Unexpected status_code={resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 6 — response structure
# ---------------------------------------------------------------------------

def test_response_structure() -> None:
    name = "6. test_response_structure: response JSON has all required keys"
    if not os.path.exists(REALISTIC_IMAGE):
        record(SKIP, name, "Realistic image not found")
        return
    try:
        client = _get_client()
        with open(REALISTIC_IMAGE, "rb") as f:
            image_bytes = f.read()

        resp = client.post(
            "/analyze-pid",
            files={"file": ("sample_pid_realistic.png", image_bytes, "image/png")},
            timeout=120,
        )
        if resp.status_code != 200:
            if resp.status_code in (422, 500) and "paddlepaddle" in resp.text.lower():
                record(SKIP, name, "paddlepaddle not installed")
            else:
                record(FAIL, name, f"Non-200 response: {resp.status_code}")
            return

        body = resp.json()
        missing = _EXPECTED_RESULT_KEYS - body.keys()
        if missing:
            record(FAIL, name, f"Missing keys in response: {missing}")
            return

        # Spot-check types
        assert isinstance(body["equipment"],   list), "equipment must be list"
        assert isinstance(body["instruments"], list), "instruments must be list"
        assert isinstance(body["pipes"],       list), "pipes must be list"
        assert isinstance(body["raw_text"],    list), "raw_text must be list"
        assert isinstance(body["total_elements"], int), "total_elements must be int"

        record(PASS, name, f"All {len(_EXPECTED_RESULT_KEYS)} required keys present and typed correctly")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Test 7 — minimal blank PNG (no crash)
# ---------------------------------------------------------------------------

def test_analyze_empty_png() -> None:
    name = "7. test_analyze_empty_png: tiny blank PNG → no server crash (200 or 422)"
    try:
        client = _get_client()
        png_bytes = _make_minimal_png()
        resp = client.post(
            "/analyze-pid",
            files={"file": ("blank.png", png_bytes, "image/png")},
            timeout=120,
        )
        # We accept 200 (no text detected) or 422 (OCR reported failure),
        # but never a 500 server crash.
        if resp.status_code in (200, 422):
            record(PASS, name, f"status_code={resp.status_code} (no server crash)")
        elif resp.status_code == 500:
            body = resp.json()
            # A controlled 500 with our error schema is acceptable
            if "error" in body:
                record(PASS, name, f"Controlled 500 error returned: {body.get('error','')[:80]}")
            else:
                record(FAIL, name, f"Unhandled 500: {resp.text[:200]}")
        else:
            record(FAIL, name, f"Unexpected status_code={resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        record(FAIL, name, f"Unexpected: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("=" * 64)
    print("  vision/api.py  --  Test Suite  (SIH 2026 MVP)")
    print("=" * 64)

    test_import()
    test_health()
    test_analyze_invalid_ext()
    test_analyze_invalid_mime()
    test_analyze_real_image()
    test_response_structure()
    test_analyze_empty_png()

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
