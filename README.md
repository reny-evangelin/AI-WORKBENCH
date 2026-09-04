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

```text
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

## 🚀 Member 2 Local Development Setup

### Prerequisites

- Python 3.11+ (Python 3.13 tested)
- [Ollama](https://ollama.com) installed and running locally
- Git
- WSL2 / Linux or Windows environment

### 1. Clone & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/reny-evangelin/AI-WORKBENCH.git
cd AI-WORKBENCH

# Switch to Member 2 branch
git checkout member-2-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On WSL/Linux:
source .venv/bin/activate

# On Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements-dev.txt
pip check
```

### 3. Setup Environment Variables

```bash
cp .env.example .env
```

### 4. Verify Ollama & Model

Check if Ollama is running and has the required model pulled:

```bash
ollama list
```

Expected output:
```text
NAME                  ID              SIZE      MODIFIED
qwen2.5-coder:1.5b    d7372fd82851    986 MB    ...
```

If missing, pull the target model:
```bash
ollama pull qwen2.5-coder:1.5b
```

### 5. Run Health Check Script

```bash
python scripts/check_ollama.py
```

Expected output:
```text
=======================================================
  SIH117 -- Member 2: Ollama Service Health Check
=======================================================

[1/4] Checking Ollama endpoint (http://localhost:11434) ...
  [OK] Ollama server reachable

[2/4] Checking Ollama API response ...
  [OK] Ollama API responding

[3/4] Checking model 'qwen2.5-coder:1.5b' availability ...
  [OK] Model qwen2.5-coder:1.5b available

[4/4] Testing sample generation ...
  Response: Ollama environment is READY.
  [OK] Test generation successful

=======================================================
  Ollama environment is READY.
=======================================================
```

### 6. Run Unit & Integration Tests

```bash
# Run unit tests only (runs offline without Ollama)
pytest -m "not integration"

# Run all tests (including Ollama integration tests)
pytest
```

---

## 📁 Repository Layout (Member 2)

```text
sih117-ai/
│
├── agent/
│   ├── __init__.py         → Public agent exports (run_agent, AgentRequest, AgentResponse)
│   ├── config.py           → Environment configuration loader
│   ├── exceptions.py       → Custom agent domain exceptions
│   ├── schemas.py          → Pydantic request & response models
│   ├── prompts.py          → Engineering system prompts and ChatPromptTemplate
│   ├── llm.py              → ChatOllama LLM factory
│   ├── chains.py           → LCEL chain construction & run_agent_request
│   ├── ollama_client.py    → Ollama connection layer abstraction
│   └── graph/
│       ├── __init__.py     → Graph package exports
│       ├── state.py        → AgentState TypedDict definition
│       ├── router.py       → Deterministic route intent classifier
│       ├── nodes.py        → Input validation, general response, placeholder & finalizer nodes
│   ├── tools/
│   │   ├── __init__.py     → Tool package exports
│   │   ├── interfaces.py   → ToolResult schema and Member capability stubs
│   │   └── registry.py     → Central safe tool registry (prevents arbitrary execution)
│   └── graph/
│       ├── __init__.py     → Graph package exports
│       ├── state.py        → AgentState TypedDict definition
│       ├── router.py       → Deterministic route intent classifier
│       ├── nodes.py        → Planning, action selection, tool execution & finalizer nodes
│       └── workflow.py     → Reason → Act → Observe LangGraph workflow construction & run_agent API
├── main.py                 → Interactive CLI application for Member 2 agent
├── scripts/
│   └── check_ollama.py     → Ollama service health check
│
├── tests/
│   ├── test_config.py      → Unit tests for configuration
│   ├── test_ollama.py      → Integration tests for Ollama
│   ├── test_schemas.py     → Unit tests for Pydantic schemas
│   ├── test_llm.py         → Unit tests for LLM factory
│   ├── test_chains.py      → Unit & integration tests for LCEL chains
│   ├── test_graph.py       → Unit & integration tests for LangGraph workflow
│   ├── test_conversation.py → Unit & integration tests for conversational flow & history
│   └── test_agentic.py    → Unit & integration tests for Phase 3 Agentic Engine
│
├── .github/
│   └── workflows/
│       └── ci.yml          → GitHub Actions CI workflow
│
├── .env.example            → Sample environment template
├── .env                    → Environment file (git-ignored)
├── .gitignore              → Git ignore patterns
├── pytest.ini              → Pytest marker configuration
├── requirements.txt        → Core production requirements
└── README.md

---

## ⚡ Status & Milestones

- **Phase 2.1 Complete**: Built clean LangChain application layer with Pydantic schemas (`AgentRequest`, `AgentResponse`), standard prompt template, and LCEL chain pipeline.
- **Phase 2.2 Complete**: Built LangGraph orchestration workflow with state management, deterministic router, placeholder nodes, and public `run_agent` API.
- **Phase 2.3A Complete**: Intelligent Conversational LLM Agent with natural greeting generation, multi-turn memory, and interactive CLI.
- **Phase 3 Complete**: Agentic Planning + Reasoning + Action Engine featuring:
  - LLM = Brain (Planning & Reasoning), LangGraph = Controller, Tools = Actions
  - Extended `AgentState` with plan, tool inputs/results, and observations
  - `AgentDecision` and `PlanStep` structured Pydantic decision models
  - Centralized safe `ToolRegistry` and `ToolResult` interface stubs (`analyze_pid`, `search_knowledge`, `generate_pdf`, `generate_docx`, `generate_excel`)
  - Tool execution safety: Strict rejection of arbitrary Python / shell / command execution
  - Reason → Act → Observe loop with bounded `MAX_ITERATIONS = 5` limit
  - Full test suite coverage (46 total tests passing)

---

## 📄 License

This project is licensed under the terms described in the [LICENSE](./LICENSE) file.
