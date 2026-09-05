"""
vision/api.py
=============
FastAPI application for P&ID image analysis (SIH 2026 MVP).

Endpoints
---------
GET  /health          — Liveness check.
POST /analyze-pid     — Upload an image, run the full pipeline, return JSON.

Pipeline (per request)
----------------------
  uploaded image
      → vision.ocr.run_ocr()
      → vision.pid.detect_pid_elements()
      → vision.parser.parse_pid_output()
      → vision.schemas.PIDAnalysisResult.from_parser_dict()
      → JSON response

Design decisions
----------------
- No authentication, no database, no cloud APIs (MVP scope).
- Temporary file is written to the OS temp directory and deleted after use.
- All pipeline errors are caught and returned as structured JSON (HTTP 422/500).
- The OCR engine singleton is initialised once at startup (lifespan event).
- Accepted MIME types: image/png, image/jpeg, image/bmp, image/tiff, image/webp.
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from vision.ocr_subprocess import get_ocr_worker, reconstruct_ocr_result
from vision.pid     import detect_pid_elements
from vision.parser  import parse_pid_output
from vision.schemas import PIDAnalysisResult, PIDAnalysisError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Accepted content types / extensions
# ---------------------------------------------------------------------------
_ACCEPTED_MIME = frozenset({
    "image/png", "image/jpeg", "image/jpg",
    "image/bmp", "image/tiff", "image/webp",
})
_ACCEPTED_EXT = frozenset({
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"
})

# ---------------------------------------------------------------------------
# Lifespan: warm up the OCR engine once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the OCR worker subprocess before the server accepts requests."""
    logger.info("API startup: launching OCR worker subprocess…")
    worker = get_ocr_worker()
    # Trigger a lightweight warm-up ping — starts the subprocess and loads the model
    # If it fails, the server still starts; /analyze-pid will return a clear error
    test_result = worker.run_ocr("")   # empty path → fast failure inside worker
    if test_result.get("success") is False and "worker" not in (test_result.get("error") or "").lower():
        # Worker started but OCR failed on empty path — that's expected
        logger.info("OCR worker subprocess ready.")
    elif not worker._available:
        logger.warning(
            "OCR worker unavailable (likely DLL conflict on Windows). "
            "P&ID analysis will return an error. All other features work normally."
        )
    else:
        logger.info("OCR worker subprocess started.")
    yield
    # Shutdown: terminate the worker subprocess cleanly
    logger.info("API shutdown: terminating OCR worker subprocess…")
    worker.shutdown()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="P&ID Analysis API",
    description="Upload a P&ID image and receive structured tag extraction results.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_upload(file: UploadFile) -> None:
    """Raise HTTPException(422) if the uploaded file is not an accepted image."""
    # Check MIME type reported by the client
    ct = (file.content_type or "").lower().strip()
    if ct and ct not in _ACCEPTED_MIME:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file type: '{ct}'. "
                f"Accepted types: {sorted(_ACCEPTED_MIME)}"
            ),
        )

    # Also check the filename extension as a fallback
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in _ACCEPTED_EXT:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file extension: '{ext}'. "
                f"Accepted extensions: {sorted(_ACCEPTED_EXT)}"
            ),
        )

    if not ct and not ext:
        raise HTTPException(
            status_code=422,
            detail="Cannot determine file type: no content-type header and no file extension.",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health() -> JSONResponse:
    """Liveness check — always returns HTTP 200 with ``{"status": "ok"}``."""
    return JSONResponse(content={"status": "ok"})


@app.post(
    "/analyze-pid",
    tags=["Analysis"],
    response_model=PIDAnalysisResult,
    responses={
        422: {"model": PIDAnalysisError, "description": "Invalid file or processing error"},
        500: {"model": PIDAnalysisError, "description": "Unexpected server error"},
    },
    summary="Analyse a P&ID image",
    description=(
        "Upload a P&ID image (PNG/JPEG/BMP/TIFF/WEBP). "
        "The server runs OCR, P&ID tag detection, and parsing, then returns "
        "a structured JSON result with equipment, valve, instrument, and pipe tags."
    ),
)
async def analyze_pid(
    file: UploadFile = File(..., description="P&ID image file to analyse"),
) -> JSONResponse:
    """
    Full pipeline:
      1. Validate the upload.
      2. Save to a temp file.
      3. Run OCR.
      4. Run P&ID detection.
      5. Parse combined results.
      6. Validate via Pydantic schema.
      7. Return JSON.
      8. Delete the temp file.
    """
    # ── 1. Validate ──────────────────────────────────────────────────────────
    _validate_upload(file)

    # Determine a safe extension for the temp file
    filename  = file.filename or "upload.png"
    ext       = os.path.splitext(filename)[1].lower() or ".png"

    tmp_path: str | None = None
    try:
        # ── 2. Save to temp file ─────────────────────────────────────────────
        suffix   = f"_{uuid.uuid4().hex}{ext}"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="pid_")
        try:
            contents = await file.read()
            with os.fdopen(fd, "wb") as fh:
                fh.write(contents)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save uploaded file: {exc}",
            )

        # ── 3. OCR (via subprocess to avoid WinError 127 DLL conflict) ────────
        worker = get_ocr_worker()
        raw = worker.run_ocr(tmp_path)
        ocr_result = reconstruct_ocr_result(raw)
        if not ocr_result.success:
            error_msg = ocr_result.error or "OCR failed with unknown error"
            logger.error("OCR failed for upload '%s': %s", filename, error_msg)
            return JSONResponse(
                status_code=422,
                content=PIDAnalysisError(
                    error=error_msg,
                    image_path=filename,
                    stage="ocr",
                ).model_dump(),
            )

        # ── 4. P&ID detection ────────────────────────────────────────────────
        pid_data = detect_pid_elements(ocr_result)

        # ── 5. Parse ─────────────────────────────────────────────────────────
        parsed = parse_pid_output(ocr_result, pid_data)

        # ── 6. Validate via schema ───────────────────────────────────────────
        result = PIDAnalysisResult.from_parser_dict(parsed, image_path=filename)

        # ── 7. Return JSON ───────────────────────────────────────────────────
        return JSONResponse(content=result.model_dump())

    except HTTPException:
        raise  # re-raise FastAPI validation errors as-is

    except Exception as exc:
        logger.exception("Unexpected error processing upload '%s'", filename)
        return JSONResponse(
            status_code=500,
            content=PIDAnalysisError(
                error=f"Unexpected server error: {type(exc).__name__}: {exc}",
                image_path=filename,
                stage="server",
            ).model_dump(),
        )

    finally:
        # ── 8. Clean up temp file ────────────────────────────────────────────
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("Temp file removed: %s", tmp_path)
            except OSError as exc:
                logger.warning("Could not remove temp file %s: %s", tmp_path, exc)


# ---------------------------------------------------------------------------
# Entrypoint (for direct `python vision/api.py` usage)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("vision.api:app", host="0.0.0.0", port=8000, reload=False)
