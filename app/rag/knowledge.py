"""Knowledge base: seed runbooks/past incidents and retrieve relevant context.

In a real system these would come from your wiki, runbooks, and resolved-incident
history. Here we seed a few representative documents to demonstrate RAG.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.rag.store import get_vector_store

# A small starter knowledge base. Each doc has a stable `title` used as its id,
# so re-seeding upserts (no duplicates).
RUNBOOKS: list[Document] = [
    Document(
        page_content=(
            "Runbook: Database connection pool exhaustion. Symptoms: 'connection "
            "pool exhausted', timeouts connecting to DB, high connection count near "
            "max. Cause: pool max too low for traffic, or connections not released. "
            "Mitigation: raise pool max, add idle timeout, restart leaking service. "
            "Long-term: connection pooling with dynamic sizing, monitor pool metrics."
        ),
        metadata={"title": "runbook-db-pool-exhaustion", "type": "runbook"},
    ),
    Document(
        page_content=(
            "Runbook: Upstream service unavailable / cascading failure. When a "
            "downstream service (e.g. payment) fails because an upstream one "
            "(checkout) is down, treat the upstream as the root cause. Mitigation: "
            "circuit breakers, timeouts, retries with backoff, graceful degradation."
        ),
        metadata={"title": "runbook-cascading-failure", "type": "runbook"},
    ),
    Document(
        page_content=(
            "Past incident INC-204: Checkout latency spike caused by Redis cache "
            "misses after a deploy flushed the cache. Fix: warm the cache on deploy, "
            "add cache-hit ratio alerts. Severity SEV-3."
        ),
        metadata={"title": "incident-204", "type": "past_incident"},
    ),
    Document(
        page_content=(
            "Runbook: Out-of-memory (OOM) crashes. Symptoms: process killed, "
            "restart loops, memory near limit. Mitigation: increase memory limit, "
            "find leak via heap profiling, add memory alerts and autoscaling."
        ),
        metadata={"title": "runbook-oom", "type": "runbook"},
    ),
]


def seed_knowledge_base() -> int:
    """Add/refresh the starter documents in the vector store. Returns the count."""
    store = get_vector_store()
    store.add_documents(RUNBOOKS, ids=[d.metadata["title"] for d in RUNBOOKS])
    return len(RUNBOOKS)


def retrieve_context(query: str, k: int = 3) -> list[Document]:
    """Return the k most semantically similar knowledge-base documents."""
    if not query.strip():
        return []
    return get_vector_store().similarity_search(query, k=k)
