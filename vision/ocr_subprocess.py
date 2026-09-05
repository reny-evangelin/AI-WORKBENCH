"""
vision/ocr_subprocess.py
========================
Interface for running PaddleOCR in a subprocess to avoid the Windows
WinError 127 DLL conflict between PaddlePaddle and PyTorch.

Root cause
----------
The main FastAPI process loads sentence_transformers → torch → shm.dll.
When paddleocr is then imported in the same process, paddlex tries to
re-import the same DLL chain at a different state → WinError 127.

Fix
---
Start a fresh Python subprocess (vision/ocr_worker.py) that ONLY imports
paddle-related packages. That process has a clean DLL environment and
runs OCR successfully. Communication uses line-delimited JSON.

Usage
-----
    from vision.ocr_subprocess import get_ocr_worker, OCRSubprocessError

    worker = get_ocr_worker()
    result_dict = worker.run_ocr("path/to/image.png")
    # result_dict has keys: success, lines, full_text, error, image_path

The worker process is a singleton. It is started lazily on first use
and reused for all subsequent requests (warm engine, no repeated startup).
If the worker crashes, the next call restarts it automatically.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).parent.parent
_WORKER_SCRIPT = Path(__file__).parent / "ocr_worker.py"


class OCRSubprocessError(RuntimeError):
    """Raised when the OCR subprocess cannot be started or crashes."""


class OCRWorkerProcess:
    """
    Long-lived subprocess wrapper for vision/ocr_worker.py.
    Thread-safe: a lock serialises all requests.
    """

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._available = True   # False if worker fails to start at all

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _start(self) -> bool:
        """Start (or restart) the worker process. Returns True on success."""
        try:
            logger.info("[OCR-WORKER] Starting subprocess: %s", _WORKER_SCRIPT)
            self._proc = subprocess.Popen(
                [sys.executable, str(_WORKER_SCRIPT)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(_ROOT),
                text=True,
                bufsize=1,           # line-buffered
            )
            # Read the readiness signal (first JSON line)
            ready_line = self._proc.stdout.readline()
            if not ready_line:
                stderr = self._proc.stderr.read(512)
                logger.error("[OCR-WORKER] No readiness signal. stderr: %s", stderr)
                self._proc = None
                return False

            ready = json.loads(ready_line.strip())
            if ready.get("ready"):
                logger.info("[OCR-WORKER] Worker ready (PID %d).", self._proc.pid)
                return True
            else:
                # Worker sent an error on startup
                error = ready.get("error", "Unknown startup error")
                logger.error("[OCR-WORKER] Worker startup error: %s", error)
                self._proc = None
                return False

        except Exception as e:
            logger.error("[OCR-WORKER] Failed to start: %s", e)
            self._proc = None
            return False

    def _is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run_ocr(self, image_path: str, lang: str = "en") -> dict:
        """
        Send an OCR request to the worker subprocess.

        Returns a dict with keys:
          success (bool), lines (list), full_text (str), error (str|None)

        Never raises — errors are returned in the dict.
        """
        with self._lock:
            if not self._available:
                return {
                    "success": False, "lines": [], "full_text": "", "image_path": image_path,
                    "error": "OCR worker is unavailable on this system (WinError 127 DLL conflict). "
                             "The rest of the application continues to work normally."
                }

            # (Re)start if not running
            if not self._is_alive():
                ok = self._start()
                if not ok:
                    self._available = False
                    return {
                        "success": False, "lines": [], "full_text": "", "image_path": image_path,
                        "error": "OCR worker process failed to start. "
                                 "PaddleOCR may have a DLL conflict on this system."
                    }

            try:
                req = json.dumps({"image_path": image_path, "lang": lang})
                self._proc.stdin.write(req + "\n")
                self._proc.stdin.flush()
                resp_line = self._proc.stdout.readline()
                if not resp_line:
                    raise IOError("Worker closed stdout unexpectedly.")
                return json.loads(resp_line.strip())
            except Exception as e:
                logger.error("[OCR-WORKER] Communication error: %s", e)
                # Kill the broken process so the next call restarts it
                try:
                    self._proc.kill()
                except Exception:
                    pass
                self._proc = None
                return {
                    "success": False, "lines": [], "full_text": "", "image_path": image_path,
                    "error": f"OCR worker communication error: {e}"
                }

    def shutdown(self):
        """Gracefully terminate the worker process."""
        with self._lock:
            if self._is_alive():
                try:
                    self._proc.stdin.write(json.dumps({"cmd": "exit"}) + "\n")
                    self._proc.stdin.flush()
                    self._proc.wait(timeout=5)
                except Exception:
                    self._proc.kill()
                finally:
                    self._proc = None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_worker: Optional[OCRWorkerProcess] = None
_worker_lock = threading.Lock()


def get_ocr_worker() -> OCRWorkerProcess:
    """Return the singleton OCR worker process (creates on first call)."""
    global _worker
    if _worker is None:
        with _worker_lock:
            if _worker is None:
                _worker = OCRWorkerProcess()
    return _worker


def reconstruct_ocr_result(data: dict):
    """
    Convert a worker JSON response dict back into the OCRResult dataclass
    so that the rest of the pipeline (pid.py, parser.py) is unchanged.
    """
    from vision.ocr import OCRResult, OCRLine
    lines = [
        OCRLine(
            text=ln["text"],
            confidence=ln.get("confidence", -1.0),
            polygon=ln.get("polygon", []),
        )
        for ln in data.get("lines", [])
    ]
    return OCRResult(
        image_path=data.get("image_path", ""),
        success=data.get("success", False),
        lines=lines,
        full_text=data.get("full_text", ""),
        error=data.get("error"),
    )
