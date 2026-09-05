"""
vision/parser.py
================
Parser module for the SIH 2026 MVP vision pipeline.

Responsibilities
----------------
- Accept an OCRResult and a P&ID detection dict (from pid.detect_pid_elements).
- Normalize detected tags (strip whitespace, upper-case).
- Deduplicate entries within each category (by tag string).
- Produce a consistent, clean Python dictionary ready for API serialisation.
- Handle missing or empty inputs safely — never raises.

Caller contract
---------------
    from vision.parser import parse_pid_output
    from vision.ocr    import run_ocr
    from vision.pid    import detect_pid_elements

    ocr_result = run_ocr("data/sample_pid/diagram.png")
    pid_data   = detect_pid_elements(ocr_result)
    parsed     = parse_pid_output(ocr_result, pid_data)
    # parsed is a plain dict — safe to pass to json.dumps or Pydantic

Output structure
----------------
{
    "document_type": "P&ID",
    "equipment":    [{"tag": str, "confidence": float, "original_text": str}, ...],
    "pumps":        [...],
    "valves":       [...],
    "instruments":  [...],
    "pipes":        [...],
    "raw_text":     [str, ...]   # every non-empty OCR line, deduplicated
}
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases (kept simple so the module has zero extra dependencies)
# ---------------------------------------------------------------------------
_PIDDict  = Dict[str, List[Dict[str, Any]]]
_Parsed   = Dict[str, Any]

# Categories that the P&ID detection module can produce.
_PID_CATEGORIES = ("equipment", "pumps", "valves", "instruments", "pipes")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_tag(tag: str) -> str:
    """Strip surrounding whitespace and force uppercase."""
    return tag.strip().upper()


def _deduplicate(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return *items* with duplicate tags removed.

    The first occurrence of each tag is kept.  Comparison is
    case-insensitive and whitespace-insensitive.
    """
    seen: set = set()
    result: List[Dict[str, Any]] = []
    for item in items:
        key = _normalize_tag(item.get("tag", ""))
        if not key:
            continue           # skip items with empty/missing tag
        if key not in seen:
            seen.add(key)
            # Return a clean copy with the normalised tag
            result.append({
                "tag":           key,
                "confidence":    round(float(item.get("confidence", -1.0)), 4),
                "original_text": item.get("original_text", ""),
            })
    return result


def _clean_raw_text(lines: list) -> List[str]:
    """Extract unique, non-empty text strings from OCR lines.

    ``lines`` is expected to be a list of :class:`~vision.ocr.OCRLine`
    objects, but the function only calls ``.text`` on each element so it
    works with any duck-typed equivalent.
    """
    seen: set = set()
    result: List[str] = []
    for line in lines:
        text = getattr(line, "text", "")
        if not isinstance(text, str):
            continue
        text = text.strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pid_output(
    ocr_result,               # vision.ocr.OCRResult — duck-typed for flexibility
    pid_data: Optional[_PIDDict] = None,
) -> _Parsed:
    """Combine OCR and P&ID detection results into a clean structured dict.

    Parameters
    ----------
    ocr_result:
        An :class:`~vision.ocr.OCRResult` instance (or any object with
        ``.success``, ``.lines``, ``.image_path`` attributes).
        Pass ``None`` to receive an empty-but-valid result.
    pid_data:
        The dict returned by :func:`~vision.pid.detect_pid_elements`.
        Each value is a list of detection dicts with at least the keys
        ``"tag"``, ``"confidence"``, and ``"original_text"``.
        Pass ``None`` or ``{}`` for an empty result.

    Returns
    -------
    dict
        Always returns a valid dict — never raises.

    Notes
    -----
    - Tags are normalised (uppercased, stripped).
    - Duplicates within each category are removed (first occurrence kept).
    - ``raw_text`` contains every unique OCR line from the image.
    - If ``ocr_result`` is ``None`` or ``success`` is ``False``, the
      ``raw_text`` list will be empty and the error is logged, but the
      function still returns a structurally valid dict.
    """
    parsed: _Parsed = {
        "document_type": "P&ID",
        "equipment":    [],
        "pumps":        [],
        "valves":       [],
        "instruments":  [],
        "pipes":        [],
        "raw_text":     [],
    }

    # ── 1. Raw OCR text ──────────────────────────────────────────────────────
    if ocr_result is None:
        logger.warning("parse_pid_output received None as ocr_result; returning empty structure.")
        return parsed

    success = getattr(ocr_result, "success", False)
    if not success:
        error = getattr(ocr_result, "error", "unknown error")
        logger.warning("parse_pid_output: OCR result is unsuccessful (%s); raw_text will be empty.", error)
        # Still proceed — pid_data may have been pre-computed elsewhere
    else:
        lines = getattr(ocr_result, "lines", []) or []
        parsed["raw_text"] = _clean_raw_text(lines)

    # ── 2. P&ID elements ─────────────────────────────────────────────────────
    if not pid_data:
        logger.info("parse_pid_output: pid_data is empty or None; element lists will be empty.")
        return parsed

    for category in _PID_CATEGORIES:
        raw_items: List[Dict[str, Any]] = pid_data.get(category, []) or []
        parsed[category] = _deduplicate(raw_items)

    logger.info(
        "parse_pid_output complete — equipment:%d pumps:%d valves:%d instruments:%d pipes:%d raw_text:%d",
        len(parsed["equipment"]),
        len(parsed["pumps"]),
        len(parsed["valves"]),
        len(parsed["instruments"]),
        len(parsed["pipes"]),
        len(parsed["raw_text"]),
    )
    return parsed
