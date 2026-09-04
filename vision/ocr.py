"""
vision/ocr.py
=============
OCR module for the Member 1 Vision pipeline (SIH 2026 MVP).

Responsibilities
----------------
- Accept an image path (str or Path).
- Initialise PaddleOCR 3.7 for **local** inference (no cloud API, no LLM).
- Run text detection + recognition with optional image preprocessing.
- Return a structured ``OCRResult`` dataclass with per-line text, confidence,
  and bounding-polygon coordinates.
- Handle every failure mode with a precise, actionable error message.

Caller contract (for pid.py)
-----------------------------
    from vision.ocr import run_ocr, OCRResult, OCRLine

    result: OCRResult = run_ocr("data/sample_pid/diagram.png")
    if result.success:
        for line in result.lines:
            print(f"[{line.confidence:.3f}] {line.text}")
    else:
        print("OCR failed:", result.error)

Environment requirements
------------------------
    paddleocr  >= 3.7.0   (wrapper + pipeline)
    paddlex    >= 3.7.0   (underlying inference framework)
    paddlepaddle >= 3.0.0 (C++ inference engine — CPU build)

    Install engine:  pip install paddlepaddle==3.3.0   (CPU)
                     pip install paddlepaddle-gpu       (CUDA)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported image extensions
# ---------------------------------------------------------------------------
_SUPPORTED_EXTS = frozenset(
    {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
)

# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------


@dataclass
class OCRLine:
    """A single recognised text line from the image.

    Attributes
    ----------
    text : str
        Recognised text string.
    confidence : float
        Recognition confidence in ``[0.0, 1.0]``.  ``-1.0`` when unavailable.
    polygon : list[list[float]]
        Bounding polygon as ``[[x1,y1], [x2,y2], ...]`` (typically 4 points).
        Empty list when coordinates are unavailable.
    """

    text: str
    confidence: float = -1.0
    polygon: List[List[float]] = field(default_factory=list)


@dataclass
class OCRResult:
    """Structured output of a single OCR run.

    Attributes
    ----------
    image_path : str
        Absolute path (or original string) of the processed image.
    success : bool
        ``True`` when OCR completed without fatal errors.
    lines : list[OCRLine]
        Recognised text lines, ordered approximately top-to-bottom.
    full_text : str
        All recognised text joined by newlines (convenience accessor).
    error : str | None
        Human-readable error message when ``success`` is ``False``.
    """

    image_path: str
    success: bool
    lines: List[OCRLine] = field(default_factory=list)
    full_text: str = ""
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_paddlepaddle() -> None:
    """Raise ``RuntimeError`` with install instructions if paddlepaddle is absent."""
    try:
        import paddle  # noqa: F401
    except ModuleNotFoundError:
        raise RuntimeError(
            "The 'paddlepaddle' inference engine is not installed.\n\n"
            "Install it with one of:\n"
            "  pip install paddlepaddle==3.3.0          # CPU-only (recommended for MVP)\n"
            "  pip install paddlepaddle-gpu             # GPU (requires CUDA)\n\n"
            "After installation, restart Python and re-run this module."
        )


def _validate_image_path(image_path: str | Path) -> Path:
    """Return a resolved ``Path`` for ``image_path`` if it is a valid image file.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    IsADirectoryError
        If the path points to a directory rather than a file.
    ValueError
        If the file extension is not in the supported set.
    """
    if not image_path:
        raise FileNotFoundError("Image path must not be empty.")

    p = Path(image_path).resolve()

    if not p.exists():
        raise FileNotFoundError(
            f"Image file not found: {p}\n"
            "Check that the path is correct and the file exists."
        )

    if p.is_dir():
        raise IsADirectoryError(
            f"Expected an image file but got a directory: {p}"
        )

    if p.suffix.lower() not in _SUPPORTED_EXTS:
        raise ValueError(
            f"Unsupported image format: '{p.suffix}' ({p.name})\n"
            f"Supported formats: {sorted(_SUPPORTED_EXTS)}"
        )

    return p


def _build_ocr_engine(
    lang: str = "en",
    *,
    enable_preprocessing: bool = True,
) -> object:
    """Initialise and return a ``PaddleOCR`` 3.7 instance for local inference.

    Parameters
    ----------
    lang : str
        Language code for the recognition model (default ``"en"``).
        Supported by PP-OCRv6: ``"ch"``, ``"en"``, ``"japan"``, ``"chinese_cht"``,
        and most Latin-script languages.  Other languages fall back to PP-OCRv5.
    enable_preprocessing : bool
        When ``True`` (default), enables:
        - Document orientation classification (auto-rotates landscape/portrait).
        - Text-line orientation classification (corrects 180° flipped lines).
        Document unwarping is **not** enabled by default because it requires an
        additional model download and is rarely needed for clean P&ID scans.

    Raises
    ------
    RuntimeError
        If paddlepaddle is not installed, or if the PaddleOCR engine fails
        to initialise for any other reason.
    """
    # --- 0. Pre-flight: verify paddlepaddle is importable ---
    _check_paddlepaddle()

    # --- 1. Suppress the external network connectivity check ---
    # PaddleX 3.x pings model hosting servers at startup unless this env var
    # is set.  Models are downloaded once and then cached in ~/.paddlex/.
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

    # Windows fix: disable oneDNN/mkldnn by default to avoid PaddleX 3.x
    # PIR executor crash:  "ConvertPirAttribute2RuntimeAttribute not support
    # [pir::ArrayAttribute<pir::DoubleAttribute>]" (onednn_instruction.cc:118)
    # This env var must be set before paddle is imported.
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")

    # --- 2. Import the PaddleOCR 3.7 pipeline wrapper ---
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "Failed to import paddleocr. "
            "Ensure it is installed:  pip install paddleocr==3.7.0"
        ) from exc

    # --- 3. Initialise the pipeline ---
    try:
        ocr = PaddleOCR(
            lang=lang,
            # Preprocessing: orientation correction for rotated/scanned docs.
            use_doc_orientation_classify=enable_preprocessing,
            # Doc unwarping off by default (extra model, rarely needed for P&IDs).
            use_doc_unwarping=False,
            # Text-line orientation: corrects upside-down text lines.
            use_textline_orientation=enable_preprocessing,
            # Windows fix: disable mkldnn to avoid oneDNN PIR executor crash.
            # Confirmed root cause: PaddlePaddle 3.3.x + PIR executor on Windows
            # triggers an unimplemented oneDNN instruction at inference time.
            # Setting enable_new_ir=False falls back to the legacy executor.
            enable_mkldnn=False,
            engine_config={"enable_new_ir": False},
        )
    except RuntimeError as exc:
        msg = str(exc)
        if "paddlepaddle" in msg or "paddle_static" in msg or "paddle" in msg.lower():
            raise RuntimeError(
                "PaddleOCR engine initialisation failed due to a paddlepaddle error.\n\n"
                f"Original error: {exc}\n\n"
                "Possible causes:\n"
                "  1. paddlepaddle not installed → pip install paddlepaddle==3.3.0\n"
                "  2. Version mismatch between paddlepaddle and paddleocr/paddlex\n"
                "  3. CUDA/GPU driver mismatch (use CPU build to rule this out)\n"
            ) from exc
        # Re-raise unknown RuntimeErrors as-is.
        raise RuntimeError(
            f"PaddleOCR initialisation failed: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error while initialising PaddleOCR: {type(exc).__name__}: {exc}"
        ) from exc

    return ocr


def _parse_results(raw_results: list, image_path: str) -> OCRResult:
    """Convert PaddleOCR 3.7 ``predict()`` output into an :class:`OCRResult`.

    PaddleOCR 3.7 ``predict()`` returns a list of result objects (one per
    input image).  Each result object exposes:

    - ``rec_texts``  : ``list[str]``   — recognised text per detected box
    - ``rec_scores`` : ``list[float]`` — confidence per box
    - ``rec_polys``  : ``list[ndarray|list]`` — bounding polygon per box

    Raises
    ------
    RuntimeError
        If result parsing fails unexpectedly (not silently swallowed).
    """
    if not raw_results:
        logger.warning("PaddleOCR returned an empty result list for: %s", image_path)
        return OCRResult(
            image_path=image_path,
            success=True,
            lines=[],
            full_text="",
        )

    lines: List[OCRLine] = []

    for page_result in raw_results:
        # PaddleX result objects support dict-style .get() access.
        try:
            texts = page_result.get("rec_texts", []) or []
            scores = page_result.get("rec_scores", []) or []
            polys = page_result.get("rec_polys", []) or []
        except AttributeError:
            # Fallback for result shapes that use attribute access.
            logger.debug(
                "Result object type %s does not support .get(); "
                "falling back to getattr.",
                type(page_result).__name__,
            )
            texts = getattr(page_result, "rec_texts", []) or []
            scores = getattr(page_result, "rec_scores", []) or []
            polys = getattr(page_result, "rec_polys", []) or []

        for idx, text in enumerate(texts):
            if not isinstance(text, str) or not text.strip():
                continue  # skip blank / non-string detections

            confidence: float = -1.0
            if idx < len(scores):
                try:
                    confidence = round(float(scores[idx]), 4)
                except (TypeError, ValueError):
                    confidence = -1.0

            polygon: List[List[float]] = []
            if idx < len(polys):
                try:
                    polygon = [
                        [float(pt[0]), float(pt[1])]
                        for pt in polys[idx]
                    ]
                except (TypeError, IndexError, ValueError):
                    polygon = []

            lines.append(OCRLine(
                text=text.strip(),
                confidence=confidence,
                polygon=polygon,
            ))

    full_text = "\n".join(line.text for line in lines)
    return OCRResult(
        image_path=image_path,
        success=True,
        lines=lines,
        full_text=full_text,
    )


# ---------------------------------------------------------------------------
# Module-level engine singleton
# ---------------------------------------------------------------------------

_ocr_engine: object | None = None
_engine_lang: str = ""


def _get_engine(lang: str = "en", *, enable_preprocessing: bool = True) -> object:
    """Return the cached PaddleOCR engine, building it on first use.

    The singleton is keyed on ``lang``.  If a different language is requested,
    the engine is rebuilt.
    """
    global _ocr_engine, _engine_lang
    if _ocr_engine is None or _engine_lang != lang:
        if _ocr_engine is not None:
            logger.info(
                "Language changed from '%s' to '%s'; rebuilding OCR engine.",
                _engine_lang, lang,
            )
        logger.info("Initialising PaddleOCR engine (lang=%s)...", lang)
        _ocr_engine = _build_ocr_engine(lang, enable_preprocessing=enable_preprocessing)
        _engine_lang = lang
        logger.info("PaddleOCR engine ready.")
    return _ocr_engine


def reset_engine() -> None:
    """Force the engine singleton to be rebuilt on the next ``run_ocr()`` call.

    Useful in tests or when switching languages.
    """
    global _ocr_engine, _engine_lang
    _ocr_engine = None
    _engine_lang = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_ocr(
    image_path: str | Path,
    *,
    lang: str = "en",
    enable_preprocessing: bool = True,
) -> OCRResult:
    """Run OCR on a local image file and return structured results.

    This is the primary entry-point for ``pid.py`` and the test suite.

    Parameters
    ----------
    image_path : str | Path
        Path to the image file.  Supported formats:
        PNG, JPEG, BMP, TIFF, WEBP.
    lang : str
        Language code passed to PaddleOCR (default ``"en"``).
        Use ``"ch"`` for Chinese, ``"en"`` for English, etc.
    enable_preprocessing : bool
        When ``True`` (default), applies document orientation correction and
        text-line orientation correction before running OCR.  Disable for
        speed if images are known to be upright.

    Returns
    -------
    OCRResult
        **Always** returns an ``OCRResult`` — never raises.
        Check ``result.success`` before consuming ``result.lines``.
        On failure, ``result.error`` contains the precise reason.

    Examples
    --------
    >>> result = run_ocr("data/sample_pid/diagram.png")
    >>> for line in result.lines:
    ...     print(f"[{line.confidence:.3f}] {line.text}")
    """
    image_path_str = str(image_path)

    # ── Step 1: Validate the image path ──────────────────────────────────────
    try:
        resolved = _validate_image_path(image_path)
    except FileNotFoundError as exc:
        logger.error("OCR path error (file not found): %s", exc)
        return OCRResult(image_path=image_path_str, success=False, error=str(exc))
    except IsADirectoryError as exc:
        logger.error("OCR path error (is a directory): %s", exc)
        return OCRResult(image_path=image_path_str, success=False, error=str(exc))
    except ValueError as exc:
        logger.error("OCR path error (unsupported format): %s", exc)
        return OCRResult(image_path=image_path_str, success=False, error=str(exc))

    # ── Step 2: Obtain the inference engine ───────────────────────────────────
    try:
        engine = _get_engine(lang, enable_preprocessing=enable_preprocessing)
    except RuntimeError as exc:
        logger.error("OCR engine initialisation failed: %s", exc)
        return OCRResult(image_path=image_path_str, success=False, error=str(exc))

    # ── Step 3: Run inference ─────────────────────────────────────────────────
    try:
        logger.info("Running OCR on: %s", resolved)
        raw_results = engine.predict(str(resolved))
    except RuntimeError as exc:
        logger.error("OCR inference runtime error for %s: %s", resolved, exc)
        return OCRResult(
            image_path=image_path_str,
            success=False,
            error=f"OCR inference failed: {exc}",
        )
    except Exception as exc:
        logger.error(
            "Unexpected OCR inference error for %s: %s: %s",
            resolved, type(exc).__name__, exc,
        )
        return OCRResult(
            image_path=image_path_str,
            success=False,
            error=f"Unexpected inference error ({type(exc).__name__}): {exc}",
        )

    # ── Step 4: Parse and structure the results ───────────────────────────────
    try:
        result = _parse_results(raw_results, image_path_str)
    except RuntimeError as exc:
        logger.error("OCR result parsing failed for %s: %s", resolved, exc)
        return OCRResult(image_path=image_path_str, success=False, error=str(exc))
    except Exception as exc:
        logger.error(
            "Unexpected result parsing error for %s: %s: %s",
            resolved, type(exc).__name__, exc,
        )
        return OCRResult(
            image_path=image_path_str,
            success=False,
            error=f"Result parsing error ({type(exc).__name__}): {exc}",
        )

    logger.info(
        "OCR complete: %d line(s) detected. First: %r",
        len(result.lines),
        result.lines[0].text if result.lines else "(none)",
    )
    return result
