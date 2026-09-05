"""
api/main.py — FastAPI Backend with Smart Input Router
======================================================

Architecture
------------
WEB UI  →  FastAPI  →  SmartRouter  →  Correct Processing Path  →  Agent/RAG/Tools  →  Response

SmartRouter uses deterministic Python logic — NOT LLM calls — to decide:
  - text    → direct agent
  - pdf     → text_extraction (digital) or OCR (scanned, if text density is low)
  - image   → vision/OCR pipeline
  - docx    → DOCX extraction → RAG/agent
  - xlsx    → Excel processing
  - unsupported → clear error

Supported input_types: text, pdf, image, docx, xlsx
Unsupported: csv (explicit rejection)
"""

import sys
import os
import time
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import process_request
from vision.api import lifespan as vision_lifespan

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported extensions
# ---------------------------------------------------------------------------
_IMAGE_EXTS  = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_PDF_EXT     = ".pdf"
_DOCX_EXT    = ".docx"
_XLSX_EXT    = ".xlsx"
_TEXT_EXTS   = frozenset({".txt"})
_UNSUPPORTED = frozenset({".csv"})

# Minimum character density per PDF page to consider it a "digital" PDF
# Below this threshold we trigger OCR.
_PDF_TEXT_DENSITY_THRESHOLD = 50   # chars per page


# ---------------------------------------------------------------------------
# SmartRouter
# ---------------------------------------------------------------------------

class SmartRouter:
    """
    Deterministic input router.
    Selects the minimum required processing path based on file type and user intent.
    NEVER calls Ollama/LLM to classify file types.
    """

    def __init__(self):
        self._t0 = 0.0

    def _start_timer(self):
        self._t0 = time.monotonic()
        return self._t0

    def _elapsed_ms(self) -> float:
        return (time.monotonic() - self._t0) * 1000

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def route(
        self,
        message: str,
        file_path: Optional[str],
        filename: Optional[str],
        input_type: Optional[str],   # hint from frontend
        file_type: Optional[str],    # hint from frontend (extension or mime)
    ) -> dict:
        """
        Returns a routing decision dict:
        {
            "path": "text"|"pdf_digital"|"pdf_scanned"|"image"|"docx"|"xlsx"|"error",
            "needs_ocr": bool,
            "needs_vision": bool,
            "needs_text_extraction": bool,
            "needs_rag": bool,
            "reason": str,
            "routing_ms": float,
        }
        """
        t0 = time.monotonic()

        # 1. Resolve the effective extension from filename or file_type hint
        ext = self._resolve_ext(filename, file_type)

        # 2. Reject unsupported types immediately
        if ext in _UNSUPPORTED:
            return self._decision(
                "error", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=False, needs_rag=False,
                reason=f"Unsupported file type: {ext}. CSV files are not supported."
            )

        # 3. No file uploaded → pure text chat
        if not file_path or not os.path.exists(file_path):
            return self._decision(
                "text", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=False, needs_rag=False,
                reason="No file attached — pure text chat."
            )

        # 4. Route by extension (deterministic Python)
        if ext in _IMAGE_EXTS:
            return self._route_image(message, file_path, t0)

        if ext == _PDF_EXT:
            return self._route_pdf(message, file_path, t0)

        if ext == _DOCX_EXT:
            return self._decision(
                "docx", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=True, needs_rag=True,
                reason="DOCX — extract paragraphs/tables then agent."
            )

        if ext == _XLSX_EXT:
            return self._decision(
                "xlsx", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=True, needs_rag=True,
                reason="XLSX — structured spreadsheet extraction then agent."
            )

        if ext in _TEXT_EXTS:
            return self._decision(
                "text_file", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=True, needs_rag=False,
                reason="Plain text file — read directly."
            )

        # 5. Fallback: unknown extension — treat as text chat
        return self._decision(
            "text", t0,
            needs_ocr=False, needs_vision=False,
            needs_text_extraction=False, needs_rag=False,
            reason=f"Unknown extension '{ext}' — defaulting to text chat."
        )

    # ------------------------------------------------------------------
    # Image routing
    # ------------------------------------------------------------------

    def _route_image(self, message: str, file_path: str, t0: float) -> dict:
        """Decide OCR / Vision / both based on explicit user intent."""
        msg_lower = message.lower()

        # Explicit OCR requests
        ocr_signals = ["extract text", "ocr", "read text", "get text", "text from", "text in"]
        # Explicit vision requests
        vision_signals = [
            "explain", "analyze", "understand", "describe", "what is", "what does",
            "chart", "diagram", "graph", "visual", "p&id", "piping", "circuit"
        ]

        wants_ocr    = any(s in msg_lower for s in ocr_signals)
        wants_vision = any(s in msg_lower for s in vision_signals)

        # Default for images: vision (with OCR if text keywords present)
        if not wants_ocr and not wants_vision:
            wants_vision = True

        reason_parts = []
        if wants_ocr:    reason_parts.append("OCR (user requested text extraction)")
        if wants_vision: reason_parts.append("Vision (image understanding requested)")

        return self._decision(
            "image", t0,
            needs_ocr=wants_ocr,
            needs_vision=wants_vision,
            needs_text_extraction=False,
            needs_rag=False,
            reason=" + ".join(reason_parts) or "Default image processing."
        )

    # ------------------------------------------------------------------
    # PDF routing
    # ------------------------------------------------------------------

    def _route_pdf(self, message: str, file_path: str, t0: float) -> dict:
        """Measure text density to decide between digital extraction vs OCR."""
        try:
            import pymupdf
            doc = pymupdf.open(file_path)
            page_count = len(doc)
            total_chars = sum(len(page.get_text().strip()) for page in doc)
            doc.close()

            avg_chars_per_page = total_chars / max(page_count, 1)

            if avg_chars_per_page >= _PDF_TEXT_DENSITY_THRESHOLD:
                path = "pdf_digital"
                reason = (
                    f"Digital PDF — {avg_chars_per_page:.0f} chars/page "
                    f"(threshold {_PDF_TEXT_DENSITY_THRESHOLD}). Text extraction only."
                )
                return self._decision(
                    path, t0,
                    needs_ocr=False, needs_vision=False,
                    needs_text_extraction=True, needs_rag=True,
                    reason=reason
                )
            else:
                path = "pdf_scanned"
                reason = (
                    f"Scanned PDF — only {avg_chars_per_page:.0f} chars/page. OCR required."
                )
                return self._decision(
                    path, t0,
                    needs_ocr=True, needs_vision=False,
                    needs_text_extraction=True, needs_rag=True,
                    reason=reason
                )
        except Exception as e:
            # If we cannot open the PDF at all, return a safe error
            return self._decision(
                "error", t0,
                needs_ocr=False, needs_vision=False,
                needs_text_extraction=False, needs_rag=False,
                reason=f"Cannot open PDF: {e}"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_ext(filename: Optional[str], file_type: Optional[str]) -> str:
        """Get lowercase extension from filename, falling back to file_type hint."""
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            if ext:
                return ext
        if file_type:
            ft = file_type.lower().strip().lstrip(".")
            # Normalise common aliases
            _aliases = {"jpeg": ".jpg", "jpg": ".jpg", "png": ".png", "webp": ".webp",
                        "pdf": ".pdf", "docx": ".docx", "xlsx": ".xlsx", "txt": ".txt",
                        "csv": ".csv"}
            return _aliases.get(ft, f".{ft}")
        return ""

    @staticmethod
    def _decision(
        path: str,
        t0: float,
        *,
        needs_ocr: bool,
        needs_vision: bool,
        needs_text_extraction: bool,
        needs_rag: bool,
        reason: str,
    ) -> dict:
        routing_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "[ROUTER] path=%s | OCR=%s VISION=%s TEXT=%s RAG=%s | %.1fms | %s",
            path, needs_ocr, needs_vision, needs_text_extraction, needs_rag,
            routing_ms, reason,
        )
        return {
            "path": path,
            "needs_ocr": needs_ocr,
            "needs_vision": needs_vision,
            "needs_text_extraction": needs_text_extraction,
            "needs_rag": needs_rag,
            "reason": reason,
            "routing_ms": round(routing_ms, 2),
        }


# Singleton
_router = SmartRouter()


# ---------------------------------------------------------------------------
# Process helpers — minimum-path handlers
# ---------------------------------------------------------------------------

def _process_pdf_digital(file_path: str) -> str:
    """Extract text from a digital PDF using PyMuPDF (no OCR)."""
    t0 = time.monotonic()
    try:
        import pymupdf
        doc = pymupdf.open(file_path)
        pages_text = [page.get_text().strip() for page in doc]
        doc.close()
        content = "\n\n---PAGE BREAK---\n\n".join(p for p in pages_text if p)
        logger.info("[PROCESS] PDF text extraction: %.0fms, %d chars", (time.monotonic()-t0)*1000, len(content))
        return content
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}") from e


def _process_docx(file_path: str) -> str:
    """Extract paragraphs and table text from a DOCX file."""
    t0 = time.monotonic()
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        content = "\n\n".join(paragraphs)
        logger.info("[PROCESS] DOCX extraction: %.0fms, %d chars", (time.monotonic()-t0)*1000, len(content))
        return content
    except Exception as e:
        raise RuntimeError(f"DOCX extraction failed: {e}") from e


def _process_xlsx(file_path: str) -> str:
    """Extract structured text from XLSX (all sheets, all rows)."""
    t0 = time.monotonic()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        lines = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            lines.append(f"=== Sheet: {sheet_name} ===")
            headers = [str(c.value) if c.value is not None else "" for c in ws[1]]
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_data = {h: str(v) for h, v in zip(headers, row) if v is not None}
                if row_data:
                    lines.append(", ".join(f"{k}: {v}" for k, v in row_data.items()))
        content = "\n".join(lines)
        logger.info("[PROCESS] XLSX extraction: %.0fms, %d chars", (time.monotonic()-t0)*1000, len(content))
        return content
    except Exception as e:
        raise RuntimeError(f"XLSX extraction failed: {e}") from e


def _process_txt(file_path: str) -> str:
    """Read a plain text file."""
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Text file read failed: {e}") from e


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Agent API — Smart Router", lifespan=vision_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "backend": True, "vision": True, "ollama": True}


# ---------------------------------------------------------------------------
# P&ID Analysis (Vision path — dedicated endpoint)
# ---------------------------------------------------------------------------

@app.post("/analyze-pid")
async def analyze_pid_wrapper(file: UploadFile = File(...)):
    from vision.api import analyze_pid as vision_analyze_pid
    return await vision_analyze_pid(file=file)


# ---------------------------------------------------------------------------
# MAIN CHAT ENDPOINT — Smart Routing
# ---------------------------------------------------------------------------

@app.post("/chat")
async def chat_endpoint(
    message:    str           = Form(...),
    file:       Optional[UploadFile] = File(None),
    input_type: Optional[str] = Form(None),   # "text" | "image" | "pdf" | "docx" | "xlsx"
    file_type:  Optional[str] = Form(None),   # extension hint e.g. "pdf", "png"
):
    """
    Smart routing chat endpoint.
    The frontend passes input_type and file_type so we NEVER need an LLM
    to classify the file — pure Python deterministic routing.
    """
    total_t0 = time.monotonic()
    tmp_path = None

    try:
        filename = file.filename if file else None

        # 1. Save the uploaded file to a temp path
        if file:
            ext = os.path.splitext(filename or "")[1].lower() or ".bin"
            suffix = f"_{uuid.uuid4().hex}{ext}"
            fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="chat_")
            contents = await file.read()
            with os.fdopen(fd, "wb") as fh:
                fh.write(contents)
            # Guard against zero-byte uploads
            if os.path.getsize(tmp_path) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

        # 2. Run the SmartRouter — deterministic, no LLM
        decision = _router.route(
            message=message,
            file_path=tmp_path,
            filename=filename,
            input_type=input_type,
            file_type=file_type,
        )

        path = decision["path"]

        # 3. Unsupported types — early return, no agent call
        if path == "error":
            return {
                "reply": f"❌ {decision['reason']}",
                "status": "error",
                "sources": [],
                "routing": decision,
            }

        # 4. Build enriched message for the agent depending on path
        process_t0 = time.monotonic()
        enriched_message = message
        image_for_agent = None

        if path == "text":
            # Pure text — agent handles everything
            pass

        elif path == "image":
            # Image → vision node in agent handles it
            image_for_agent = tmp_path

        elif path == "pdf_digital":
            # Extract text, prepend to message, no OCR
            pdf_text = _process_pdf_digital(tmp_path)
            if not pdf_text.strip():
                # Empty extracted text despite digital label — warn and pass as-is
                enriched_message = f"{message}\n\n[Document attached but no selectable text found]"
            else:
                enriched_message = (
                    f"{message}\n\n"
                    f"[DOCUMENT CONTENT — {filename}]\n"
                    f"{pdf_text[:8000]}"   # cap at 8000 chars to avoid context overflow
                )

        elif path == "pdf_scanned":
            # Scanned PDF — needs OCR, which happens in the agent's process_vision node
            # We pass the file as the vision input; the agent will run OCR on it
            image_for_agent = tmp_path

        elif path == "docx":
            docx_text = _process_docx(tmp_path)
            enriched_message = (
                f"{message}\n\n"
                f"[DOCUMENT CONTENT — {filename}]\n"
                f"{docx_text[:8000]}"
            )

        elif path == "xlsx":
            xlsx_text = _process_xlsx(tmp_path)
            enriched_message = (
                f"{message}\n\n"
                f"[SPREADSHEET CONTENT — {filename}]\n"
                f"{xlsx_text[:8000]}"
            )

        elif path == "text_file":
            txt = _process_txt(tmp_path)
            enriched_message = (
                f"{message}\n\n"
                f"[FILE CONTENT — {filename}]\n"
                f"{txt[:8000]}"
            )

        process_ms = (time.monotonic() - process_t0) * 1000

        # 5. Call the agent with the enriched message
        agent_t0 = time.monotonic()
        response = process_request(enriched_message, image_path=image_for_agent)
        agent_ms = (time.monotonic() - agent_t0) * 1000

        total_ms = (time.monotonic() - total_t0) * 1000

        logger.info(
            "[TOTAL] routing=%.1fms process=%.1fms agent=%.1fms TOTAL=%.1fms",
            decision["routing_ms"], process_ms, agent_ms, total_ms,
        )

        return {
            "reply": response.answer,
            "status": response.status,
            "sources": response.sources,
            "routing": {
                "path": path,
                "reason": decision["reason"],
                "routing_ms": decision["routing_ms"],
                "process_ms": round(process_ms, 1),
                "agent_ms": round(agent_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Document Upload / RAG Ingestion
# ---------------------------------------------------------------------------

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for RAG ingestion.
    Supports: PDF, DOCX, XLSX.
    Rejects: CSV and other unsupported types.
    """
    import shutil
    filename = file.filename or "upload.bin"
    ext = os.path.splitext(filename)[1].lower()

    # Reject unsupported
    if ext in _UNSUPPORTED:
        raise HTTPException(status_code=400, detail=f"CSV files are not supported for upload.")
    if ext not in {_PDF_EXT, _DOCX_EXT, _XLSX_EXT}:
        raise HTTPException(status_code=400, detail=f"Unsupported document type: {ext}. Supported: PDF, DOCX, XLSX.")

    os.makedirs("data/documents", exist_ok=True)
    path = os.path.join("data/documents", filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.path.getsize(path) == 0:
        os.remove(path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    from rag.pipeline import run_pipeline
    summary = run_pipeline("data/documents")
    return {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "status": "indexed",
        "summary": summary.get(filename, {}),
    }


# ---------------------------------------------------------------------------
# RAG Search
# ---------------------------------------------------------------------------

@app.post("/rag/search")
async def search_knowledge(query: dict):
    from rag.retriever import retrieve
    q = query.get("query", "")
    matches = retrieve(q, n_results=4)
    return [
        {
            "id": str(uuid.uuid4()),
            "document": m.get("metadata", {}).get("source_file", "unknown"),
            "section": f"Page {m.get('metadata', {}).get('page_number', '?')}",
            "text": m.get("text", ""),
            "relevance": m.get("score", 0.9),
            "category": "Knowledge",
        }
        for m in matches
    ]


# ---------------------------------------------------------------------------
# Analysis / Report Generation
# ---------------------------------------------------------------------------

@app.post("/analyze")
async def analyze_endpoint(context: dict):
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.prompts import PromptTemplate
    from pydantic import BaseModel, Field
    from typing import List, Literal
    from agent.llm import get_llm
    import json
    import datetime

    class Finding(BaseModel):
        id: str
        type: str
        finding: str
        evidence: str
        section: str
        recommendation: str
        severity: Literal["critical", "moderate", "low", "info"]

    class Ref(BaseModel):
        id: str
        document: str
        section: str
        text: str
        relevance: float
        category: str

    class AnalysisReport(BaseModel):
        summary: str
        confidence: float
        generatedAt: str
        findings: List[Finding]
        sopReferences: List[Ref]

    parser = PydanticOutputParser(pydantic_object=AnalysisReport)
    prompt = PromptTemplate(
        template=(
            "Analyze the following context (P&ID data and Knowledge Base results) "
            "and generate a structured engineering analysis report.\n\n"
            "Context:\n{context}\n\n{format_instructions}\n"
        ),
        input_variables=["context"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    llm = get_llm()
    chain = prompt | llm | parser

    try:
        report = chain.invoke({"context": json.dumps(context)})
        report.generatedAt = datetime.datetime.now().isoformat()
        return report.model_dump()
    except Exception as e:
        logger.exception("Analyze error")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Document Generation
# ---------------------------------------------------------------------------

@app.post("/generate-document")
async def generate_document():
    response = process_request("Generate a DOCX document")

    import glob
    docx_files = glob.glob("outputs/*.docx")
    if not docx_files:
        raise HTTPException(status_code=500, detail="DOCX file not generated.")

    latest_file = max(docx_files, key=os.path.getctime)
    filename = os.path.basename(latest_file)
    return {
        "file_name": filename,
        "file_type": "DOCX",
        "download_url": f"/outputs/{filename}",
        "status": "success",
    }


# ---------------------------------------------------------------------------
# Safe file opener (server-side only)
# ---------------------------------------------------------------------------

@app.get("/open-file")
async def open_file(filename: str):
    import platform, subprocess
    # Sanitise: only allow files from outputs/
    safe_name = Path(filename).name
    file_path = Path("outputs") / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        if platform.system() == "Darwin":
            subprocess.call(("open", str(file_path)))
        elif platform.system() == "Windows":
            os.startfile(str(file_path))
        else:
            subprocess.call(("xdg-open", str(file_path)))
        return {"status": "opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8001, reload=True)
