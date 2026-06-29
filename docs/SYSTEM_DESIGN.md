# System Design Review — Enterprise AI Incident Manager

A complete architectural review and interview-prep companion for this project.

---

## 1. What it is (the elevator pitch)

A multi-agent AI system that ingests raw production logs and automatically produces
a full incident analysis — root cause, severity, recommended fixes, recovery plan,
and a post-mortem — grounded in retrieved runbooks/past incidents (RAG), running
entirely on a free local LLM. **Business value: it reduces MTTR** (Mean Time To
Resolve) by automating the diagnosis work an on-call engineer does manually.

---

## 2. Architecture (end to end)

```
Client → FastAPI (JWT+RBAC, validation, rate limiting)
       → Log Pipeline (parse → normalize → correlate → analyze)
       → LangGraph multi-agent orchestrator:
           log_analyzer → monitoring → retrieval(RAG) → root_cause
           → severity → fix → recovery_planner → report_generator
              ↘ ChromaDB (vector store)   ↘ Ollama (local LLM)
       → PostgreSQL (users, incidents, logs, reports)
       → Dashboard (Chart.js) + Prometheus /metrics
```

**Request lifecycle (analyze):** authenticate (JWT) → authorize (RBAC) → rate-limit
→ load incident → build analysis → run 7-agent graph (each agent reads/writes shared
state, calls the LLM, RAG injects context) → persist Report → return validated JSON.

---

## 3. Key design decisions & trade-offs

| Decision | Why | Trade-off |
|----------|-----|-----------|
| **Modular monolith** (not microservices) | Right scale for the problem; simple to build/deploy | Must extract services later if scale demands |
| **FastAPI** | Async, type-hint validation, auto docs, AI-ecosystem standard | Less batteries-included than Django |
| **PostgreSQL (SQL)** | Structured, relational, ACID; correctness matters for incidents | Vertical scaling vs NoSQL horizontal |
| **SQLAlchemy ORM** | Productivity + SQL-injection safety + DB portability | Can hide inefficient queries (N+1) |
| **models/ vs schemas/** separation | DB shape ≠ API contract; never leak secrets | Slight duplication |
| **LangGraph for agents** | Stateful, branchable, debuggable multi-agent flows | More structure than a simple chain |
| **Local LLM (Ollama)** | Free, private, offline; swappable via one config line | Lower quality than frontier APIs |
| **RAG over fine-tuning** | Knowledge updates instantly, no training | Retrieval quality depends on chunking/embeddings |
| **Sync endpoints + threadpool** | Avoids blocking the event loop with sync DB calls | Async DB would scale further |
| **create_all (dev) vs Alembic** | Simple to learn | No safe production migrations yet (known gap) |

---

## 4. Scalability analysis

- **API**: stateless → scale horizontally behind a load balancer (run N replicas).
- **Database**: read replicas + connection pooling; index hot columns (already done on
  service/severity/correlation-id). Partition logs by time at large scale.
- **The AI analysis is the bottleneck** (7 sequential LLM calls, ~1 min). Fixes:
  run it in a **background worker (Celery/queue)** and return a job id; cache results;
  parallelize independent agents; use a faster/smaller model for triage.
- **Volume**: stream huge log files (generators) instead of loading into memory.

---

## 5. Security (defense in depth)

- **AuthN**: JWT (short access + refresh tokens). **AuthZ**: RBAC (admin/engineer/viewer).
- **Passwords**: bcrypt (salted, slow). Never stored in plaintext; never in API responses.
- **SQL injection**: prevented by the ORM's parameterized queries.
- **Prompt injection** (OWASP LLM #1): sanitize untrusted log text, delimit/label it as
  data, cap length.
- **Rate limiting**: per-IP limits on login (brute-force) and the expensive analyze endpoint.
- **Secrets**: env vars + .gitignore; startup warns on default SECRET_KEY.
- **Input validation**: Pydantic + max-length caps (DoS / token-blowup protection).

---

## 6. Observability

- **Metrics**: Prometheus `/metrics` — auto HTTP metrics + custom (incidents created,
  analyses run, LLM calls, analysis duration histogram).
- **Logs**: structured request logs.
- **Traces**: correlation IDs in logs (OpenTelemetry-ready).
- **Health**: `/health` + `/dashboard/health` (DB + LLM up?).

---

## 7. Known limitations & next steps (be honest in interviews)

- **No DB migrations** — uses create_all; add **Alembic** for production.
- **Synchronous AI** — move to a **background queue** (Celery + Redis).
- **LLM quality/timezone handling** — normalize timestamps to UTC; consider a larger model.
- **RAG** — add chunking, re-ranking, and ingest real incident history over time.
- **Tests** — add load testing and AI-output evaluation suites.
- **Deploy** — Kubernetes for orchestration; real Grafana dashboards.

---

## 8. Interview cheat sheet (practice these out loud)

**Backend / API**
- Why FastAPI over Flask/Django? (async, type-hint validation, auto docs)
- WSGI vs ASGI? Why does async matter for an AI backend? (LLM/DB waits)
- What is dependency injection and how did it make your code testable?

**Database**
- SQL vs NoSQL — why Postgres here? Why Redis (NoSQL) for caching?
- Normalization & when to denormalize. What does ACID guarantee?
- How does an ORM prevent SQL injection? What's the N+1 problem?

**AI Engineering**
- What is an LLM (next-token predictor) and why does it hallucinate?
- Tokens / context window — why did you summarize logs before the LLM?
- Chain vs graph — why LangGraph for multi-agent? What is shared state?
- RAG vs fine-tuning — when each? What's an embedding / semantic search?
- How do you get reliable structured output? (Pydantic + JSON mode)
- How do you TEST nondeterministic AI code? (mock the LLM, assert your handling)

**System Design**
- Walk through a request end to end.
- Monolith vs microservices — why, and when would you switch?
- How would you scale the AI analysis? (background workers, caching, parallelism)
- Stateless services — why do they scale better?

**DevOps / Security**
- CI vs CD. What runs in your pipeline and why is it fast?
- Container vs VM. What's a Dockerfile/Compose/volume?
- Prompt injection — what is it and how do you defend? (OWASP LLM #1)
- Defense in depth — name your layers.

---

## 9. Skills demonstrated

Backend API design · Data modeling · Auth & security · LLM application development ·
Multi-agent orchestration · RAG / vector search · Data pipelines · Observability ·
Automated testing · Containerization · CI/CD · System design & trade-off analysis.
