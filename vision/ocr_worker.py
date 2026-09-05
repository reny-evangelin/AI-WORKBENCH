"""
vision/ocr_worker.py
====================
Standalone subprocess worker that runs PaddleOCR in isolation.

This script is launched as a child process by vision/ocr_subprocess.py.
It runs in its own Python interpreter with NO torch/sentence_transformers
pre-loaded, which prevents the Windows WinError 127 DLL conflict.

Protocol (line-delimited JSON over stdin/stdout):
  → {"image_path": "...", "lang": "en"}
  ← {"success": true, "lines": [...], "full_text": "...", "error": null}
  or
  ← {"success": false, "lines": [], "full_text": "", "error": "..."}

Exit:
  Send {"cmd": "exit"} to gracefully terminate.
"""

import sys
import json
import logging
import os
from pathlib import Path

# Add project root to path (worker is run from project root)
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

logging.basicConfig(level=logging.WARNING)  # keep stdout clean for JSON protocol


def _serialize_ocr_result(result) -> dict:
    """Convert OCRResult dataclass to JSON-serializable dict."""
    return {
        "success": result.success,
        "image_path": result.image_path,
        "full_text": result.full_text,
        "error": result.error,
        "lines": [
            {
                "text": line.text,
                "confidence": line.confidence,
                "polygon": line.polygon,
            }
            for line in result.lines
        ],
    }


def main():
    # Import OCR only here — no sentence_transformers/torch in this process
    try:
        from vision.ocr import run_ocr
    except Exception as e:
        # If we can't even import ocr, write a startup error and exit
        sys.stdout.write(json.dumps({"success": False, "lines": [], "full_text": "",
                                      "error": f"Worker import failed: {e}"}) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    # Signal readiness to parent
    sys.stdout.write(json.dumps({"ready": True}) + "\n")
    sys.stdout.flush()

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError as e:
            sys.stdout.write(json.dumps({"success": False, "lines": [], "full_text": "",
                                          "error": f"Bad JSON request: {e}"}) + "\n")
            sys.stdout.flush()
            continue

        if req.get("cmd") == "exit":
            break

        image_path = req.get("image_path", "")
        lang = req.get("lang", "en")

        try:
            result = run_ocr(image_path, lang=lang)
            response = _serialize_ocr_result(result)
        except Exception as e:
            response = {"success": False, "lines": [], "full_text": "", "error": str(e)}

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
