# SIH117 — AI Engineering Assistant

> **Smart India Hackathon 2025 | Team Project**
> A local AI-powered engineering assistant capable of analyzing P&ID drawings and engineering documents, reasoning over them, and generating professional reports.

---

## 📌 Project Overview

The **AI Engineering Assistant** is a locally deployable, privacy-first system designed to assist engineers with:

- Parsing and understanding **P&ID drawings** and **engineering documents**
- Extracting structured equipment, valve, instrument, and relationship data using **OCR + Computer Vision**
- Reasoning over extracted data using a **local LLM** (via Ollama)
- Retrieving relevant engineering knowledge from a **vector knowledge base (RAG)**
- Generating professional **PDF, DOCX, and Excel reports** on demand

The system runs **fully offline** on local hardware, ensuring data security for sensitive engineering environments.

---

## 🏗️ System Architecture

```
User
  ↓
Web / Application (Member 4)
  ↓
Input Processing
  ↓
OCR + Vision + P&ID Analysis (Member 1)
  ↓
Main AI Agent — Agentic Workflow (Member 2)
  ↓
RAG / Engineering Knowledge (Member 3)
  ↓
Agentic Reasoning + Tool Calling
  ↓
Document / Excel / PDF Generation (Member 4)
  ↓
Final Answer + Sources + Generated File → User
```

---

## 👥 Team Responsibilities

| Member | Role | Responsibilities |
|--------|------|-----------------|
| **Member 1** | 👁️ Eyes — Vision & OCR | PDF/Image input, OCR, Computer Vision, P&ID analysis, structured JSON output |
| **Member 2** | 🧠 Brain — Main AI Agent | LLM agent, LangGraph workflow, intent understanding, planning, reasoning, validation, orchestration |
| **Member 3** | 📚 Memory — RAG & Knowledge | Document ingestion, chunking, embeddings, vector database, knowledge retrieval |
| **Member 4** | 🤝 Hands — App & Generation | Web application, PDF/DOCX/Excel generation, tool exposure, output handling |

---

## 📁 Repository Structure

```
sih117-ai/
│
├── agent/              → Member 2 — Main AI Agent & Agentic Workflow
│   ├── graph.py        → LangGraph workflow definition
│   ├── state.py        → Shared agent state schema
│   ├── router.py       → Intent-based routing logic
│   ├── llm.py          → Ollama LLM connection & configuration
│   ├── prompts.py      → Prompt templates
│   ├── tools.py        → Tool interfaces to Members 1, 3, 4
│   ├── validators.py   → Output validation logic
│   ├── schemas.py      → Data schemas and contracts
│   └── main.py         → Agent entry point
│
├── vision/             → Member 1 — OCR, Computer Vision, P&ID Analysis
│
├── rag/                → Member 3 — RAG Pipeline & Engineering Knowledge Base
│
├── app/                → Member 4 — Web Application & UI
│
├── tools/              → Member 4 — File Generation Tools (PDF, DOCX, Excel)
│
├── schemas/            → Shared — Integration Contracts
│   ├── pid_schema.json         → P&ID structured output schema
│   ├── rag_schema.json         → RAG retrieval response schema
│   ├── report_schema.json      → Report data schema
│   └── tool_schema.json        → Tool call schema
│
├── tests/              → Shared — Test suite
│
├── data/               → Shared — Demo data and sample documents
│
├── outputs/            → Generated output files (PDF, DOCX, Excel)
│
├── LICENSE
└── README.md
```

---

## 🔀 Git Branching Strategy

```
main
│
├── member-1-vision     → Member 1 development
├── member-2-agent      → Member 2 development (Main AI Agent)  ✅ active
├── member-3-rag        → Member 3 development
└── member-4-tools      → Member 4 development
```

- Each member develops on their own branch.
- Merge to `main` only after the module interface is tested and stable.
- The `schemas/` directory is shared — any schema changes must be agreed upon by all members before committing.
- Branch naming convention: `member-<number>-<role>` (hyphen-separated).

---

## 🔗 Integration Contracts

All four members communicate through well-defined interfaces. These contracts are version-controlled under `schemas/`.

### Member 1 → Member 2 (P&ID Analysis)

**Function:** `analyze_pid(file)`

**Output example:**
```json
{
  "equipment": [
    { "tag": "P-101", "type": "pump", "page": 3 }
  ],
  "valves": [
    { "tag": "V-101", "type": "valve", "page": 3 }
  ],
  "instruments": [
    { "tag": "PT-101", "type": "pressure_transmitter", "page": 3 }
  ],
  "relationships": [
    { "from": "P-101", "to": "V-101", "relationship": "connected_to" }
  ],
  "source": {
    "file": "plant_pid.pdf",
    "page": 3
  }
}
```

---

### Member 3 → Member 2 (Engineering Knowledge Retrieval)

**Function:** `search_knowledge(query)`

**Output example:**
```json
{
  "results": [
    {
      "content": "Relevant engineering information...",
      "source": "engineering_manual.pdf",
      "page": 25,
      "relevance": 0.91
    }
  ]
}
```

---

### Member 2 → Member 4 (Report Generation)

**Functions:**
- `generate_pdf(data)`
- `generate_docx(data)`
- `generate_excel(data)`

**Output example:**
```json
{
  "status": "success",
  "file_path": "outputs/maintenance_report_P101.xlsx",
  "file_type": "excel"
}
```

---

## 🧠 Member 2 — Agent Architecture (Main AI Agent)

Member 2 is the **central orchestrator** of the system. It does not directly process documents or generate files — instead it coordinates the other modules through a structured agentic workflow.

### Agentic Workflow

```
User Request
     ↓
Understand Intent
     ↓
Plan / Route
     ↓
┌────┴────┬────────────┐
↓         ↓            ↓
Member 1  Member 3   Member 4
P&ID/OCR   RAG       Generation
↓         ↓            ↓
└────┬────┴────────────┘
     ↓
   Reason
     ↓
  Validate
     ↓
Final Answer + Sources
```

### Technology Stack (Member 2)

| Component | Technology |
|-----------|-----------|
| Local LLM | [Ollama](https://ollama.com) |
| Initial Model | `qwen2.5-coder:1.5b` |
| Agent Framework | [LangChain](https://python.langchain.com/) |
| Workflow Framework | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| Language | Python 3.11+ |

> **Note:** The model can be swapped for a more capable model (e.g., `llama3`, `mistral`, `qwen2.5:7b`) without changing the agent architecture.

### Development Phases (Member 2)

| Phase | Goal |
|-------|------|
| Phase 1 | Basic Ollama connection (`Python → Ollama → Qwen2.5-Coder → Response`) |
| Phase 2 | LangChain integration (`LLM + Prompt + Structured Output + Tools`) |
| Phase 3 | LangGraph workflow (`START → Understand → Route → Tool → Reason → Validate → END`) |
| Phase 4 | Mock team tools (`mock_analyze_pid`, `mock_search_knowledge`, `mock_generate_excel`) |
| Phase 5 | Real integration (replace mocks with real Member 1, 3, 4 modules) |
| Phase 6 | End-to-end testing and validation |

---

## 🛡️ Anti-Hallucination Strategy

Engineering accuracy is critical. The agent **must not invent engineering facts**.

The final response must clearly distinguish between:

| Category | Meaning |
|----------|---------|
| ✅ Verified from P&ID | Directly extracted from the provided drawing |
| ✅ Verified from engineering documents | Supported by retrieved knowledge base sources |
| ⚠️ Derived / inferred | Reasoned from verified data but not directly stated |
| ❌ Unavailable | Not found in any available source |

**If information is missing, the agent must state:**

> *"I could not verify this information from the provided P&ID."*

> *"No supporting information was found in the available engineering knowledge base."*

---

## 🔄 Example End-to-End Flow

**User Request:**
> *"Analyze Pump P-101 from this P&ID and generate an Excel maintenance report."*

**Agent Workflow:**

```
1.  Understand request
2.  Identify target equipment → P-101
3.  P&ID information required → Call Member 1 (analyze_pid)
4.  Receive structured P-101 data
5.  Maintenance knowledge required → Call Member 3 (search_knowledge)
6.  Receive relevant engineering sources
7.  Combine:
      - User request
      - P&ID facts (Member 1)
      - RAG evidence (Member 3)
8.  Reason and prepare structured report data
9.  Excel output required → Call Member 4 (generate_excel)
10. Validate generated file
11. Return final answer + sources + file path
```

---

## ⚙️ Member Technology Overview

### Member 1 — Vision & OCR

| Component | Technology |
|-----------|-----------|
| PDF Parsing | PyMuPDF |
| OCR | PaddleOCR |
| Computer Vision | OpenCV |
| Image Processing | Pillow, NumPy |
| Data Validation | Pydantic |
| Vision LLM | Ollama (Vision Model) |

### Member 2 — Main AI Agent

| Component | Technology |
|-----------|-----------|
| LLM Runtime | Ollama |
| Agent Framework | LangChain |
| Workflow Engine | LangGraph |
| Initial Model | Qwen2.5-Coder 1.5B |

### Member 3 — RAG & Knowledge Base

| Component | Technology |
|-----------|-----------|
| Document Processing | LangChain document loaders |
| Chunking | Recursive text splitter |
| Embeddings | Local embedding model |
| Vector Store | ChromaDB / FAISS (TBD) |
| Retriever | LangChain retriever interface |

### Member 4 — Application & Generation

| Component | Technology |
|-----------|-----------|
| Web App | FastAPI / Streamlit (TBD) |
| PDF Generation | ReportLab / WeasyPrint |
| DOCX Generation | python-docx |
| Excel Generation | openpyxl / xlsxwriter |

---

## 🚀 Getting Started

> Each member should work on their designated branch and module. Integration happens through the defined interfaces only.

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- Git

### Clone the Repository

```bash
git clone https://github.com/<your-org>/sih117-ai.git
cd sih117-ai
```

### Member 2 — Switch to Your Branch

The `member-2-agent` branch already exists on the remote. Use the following commands:

```bash
# Fetch all remote branches
git fetch origin

# Switch to the Member 2 branch (tracks origin/member-2-agent automatically)
git checkout member-2-agent
```

Verify you are on the correct branch:

```bash
git branch
# Expected output:
#   main
# * member-2-agent
```

> **Note:** Do not run `git checkout -b member-2-agent` if the branch already exists — use `git checkout member-2-agent` instead.

### Pull the Local LLM Model (Member 2)

```bash
ollama pull qwen2.5-coder:1.5b
```

### Install Dependencies

```bash
# (Per module — each member maintains their own requirements.txt)
pip install -r agent/requirements.txt
```

---

## 📐 Design Principles

1. **Modularity** — Each member's module is independently deployable and testable.
2. **Interface-first** — Integration contracts are agreed upon before implementation begins.
3. **Hallucination prevention** — The agent must cite sources and flag missing information explicitly.
4. **Local-first** — The entire system runs offline on local hardware.
5. **Staged development** — Mock tools allow the agent to be developed before all modules are ready.
6. **Schema versioning** — All integration schemas are version-controlled in `schemas/`.

---

## 📄 License

This project is licensed under the terms described in the [LICENSE](./LICENSE) file.

---

> *Built for Smart India Hackathon 2025 | Problem Statement SIH117*
