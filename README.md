# 🛡️ Enterprise AI Production Incident Manager

> A production-grade **multi-agent AI system** that automatically analyzes production incidents — it reads raw application logs, detects anomalies, finds the **root cause**, assigns **severity**, recommends **fixes**, generates a **recovery plan**, and writes a full **post-mortem** — all running **100% locally and free** on an open-source LLM.

Inspired by the systems behind **Datadog, Splunk, PagerDuty, and New Relic**, this project demonstrates an end-to-end enterprise AI engineering stack: a secure REST backend, a multi-agent AI pipeline, retrieval-augmented generation (RAG), observability, testing, and CI/CD.

---

## ✨ What it does

Feed it messy server logs → get back a complete incident analysis:

```
INPUT (raw logs):
  2026-06-30T02:00:01 ERROR [checkout] request_id=req-9 timeout connecting to db
  2026-06-30T02:00:01 ERROR [checkout] request_id=req-9 connection pool exhausted (max=20)
  2026-06-30T02:00:02 CRITICAL [payment] request_id=req-9 payment failed

OUTPUT (AI analysis):
  ROOT CAUSE : Database connection pool exhaustion (payment failure is a downstream symptom)
  SEVERITY   : SEV-2 — major degradation
  FIX        : Raise pool max, add idle timeout, monitor pool metrics
  + full recovery plan & blameless post-mortem, saved to the database
```

The AI even **cites internal runbooks and past incidents** it retrieves from a vector store (RAG) — it learns from history.

---

## 🚀 Key Features

- **🤖 Multi-Agent AI** — 7 specialist agents (Log Analyzer, Monitoring, Root Cause, Severity, Fix Recommender, Recovery Planner, Report Generator) orchestrated with **LangGraph**, communicating through shared state.
- **🧠 RAG (memory)** — retrieves relevant runbooks & past incidents from a **ChromaDB** vector store using local embeddings, grounding the AI's reasoning.
- **🔍 Log Processing Pipeline** — parses, normalizes, and correlates raw logs (timestamps, levels, services, request-id correlation) into structured, queryable data.
- **🔐 Auth & Security** — JWT authentication, refresh tokens, and **role-based access control (RBAC)**; passwords hashed with bcrypt.
- **📊 Live Dashboard** — incident statistics, severity/status charts, and real-time system health.
- **📡 Observability** — Prometheus metrics (`/metrics`) for HTTP traffic and custom AI metrics.
- **🧪 Tested** — 21 automated tests (unit + integration + API + mocked-AI) running in **CI on every push**.
- **🐳 Containerized** — Docker + Docker Compose for the full stack (app + Postgres + Prometheus + Grafana).
- **💰 100% Free & Local** — runs an open-source LLM via **Ollama**; no API keys, no cloud bills, full privacy.

---

## 🏗️ Architecture

```
            ┌──────────────────────────────────────────────┐
   Client → │            FastAPI  (REST API)               │
            │   JWT + RBAC · validation · /docs · /metrics │
            └───────────────────┬──────────────────────────┘
                                ▼
            ┌──────────────────────────────────────────────┐
            │   Log Pipeline: parse → normalize → correlate │
            │                   → analyze                   │
            └───────────────────┬──────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────┐
   │        Multi-Agent AI Orchestrator  (LangGraph)             │
   │  log_analyzer → monitoring → retrieval(RAG) → root_cause →  │
   │     severity → fix → recovery_planner → report_generator   │
   │              │                                              │
   │       ┌──────┴──────┐         ┌────────────────────────┐   │
   │       │  ChromaDB   │◄───────►│  Ollama (llama3.1:8b)  │   │
   │       │ (RAG store) │         │   local, free LLM      │   │
   │       └─────────────┘         └────────────────────────┘   │
   └───────────────────────────────┬─────────────────────────────┘
                                    ▼
            ┌──────────────────────────────────────────────┐
            │  PostgreSQL (incidents, logs, reports, users) │
            └──────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend / API** | Python 3.13, FastAPI, Uvicorn |
| **Database** | PostgreSQL, SQLAlchemy 2.0 (ORM) |
| **Auth** | JWT (PyJWT), bcrypt, RBAC |
| **AI Orchestration** | LangChain, LangGraph |
| **LLM (local, free)** | Ollama — `llama3.1:8b` |
| **RAG / Vectors** | ChromaDB, `nomic-embed-text` embeddings |
| **Observability** | Prometheus (metrics), Grafana |
| **Frontend** | HTML + Chart.js (dashboard) |
| **Testing** | pytest |
| **DevOps** | Docker, Docker Compose, GitHub Actions (CI/CD) |

---

## ⚡ Getting Started

### Prerequisites
- Python 3.11+ (3.13 recommended)
- PostgreSQL 16
- [Ollama](https://ollama.com) (for the local LLM)

### Setup
```bash
# 1. Clone & enter
git clone https://github.com/Amitsingh-nsut2027/ai-incident-manager.git
cd ai-incident-manager

# 2. Virtual environment + dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start PostgreSQL and create the database
createdb incident_manager

# 4. Configure environment
cp .env.example .env        # then edit DATABASE_URL / SECRET_KEY as needed

# 5. Pull the local AI models (one-time)
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Run
```bash
# Start the API + dashboard
uvicorn app.main:app --reload
```
- 📊 Dashboard → http://localhost:8000/dashboard
- 📄 API docs → http://localhost:8000/docs
- 📡 Metrics → http://localhost:8000/metrics

### See it work end-to-end (easiest)
```bash
python demo.py
```
This creates an incident, parses the logs, and runs the full 7-agent AI analysis — printing the result in plain text.

---

## 🧪 Testing
```bash
pytest            # run all 21 tests
pytest --cov=app  # with coverage
```
Tests use an in-memory SQLite database and a mocked LLM, so they're fast and need no external services.

---

## 🐳 Docker (full stack)
```bash
docker compose up --build
```
Runs the app, PostgreSQL, Prometheus, and Grafana together. (Ollama runs on the host.)

---

## 📁 Project Structure
```
app/
├── api/routes/      # FastAPI endpoints (auth, incidents, dashboard, health)
├── agents/          # LangGraph multi-agent system (state, nodes, graph)
├── ai/              # LLM client, embeddings, LangChain chains
├── rag/             # vector store + knowledge base (RAG)
├── pipeline/        # log parsing, normalization, correlation
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response models
├── services/        # business logic
├── core/            # config, security, metrics
└── main.py          # app entry point
tests/               # pytest suite
monitoring/          # Prometheus config
```

---

## 🎯 Skills Demonstrated
Backend API design · Database modeling · Authentication & security · LLM application development · Multi-agent orchestration · RAG / vector search · Data pipelines · Observability · Automated testing · Containerization · CI/CD

---

## 📜 License
MIT — feel free to learn from and build on this project.
