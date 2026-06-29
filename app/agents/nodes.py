"""The 7 real AI agents (Phase 14).

Each function is a LangGraph node = one specialist agent. It reads the shared
IncidentState, calls the local LLM with a focused system prompt, and returns the
piece of the diagnosis it's responsible for.

We call the model with explicit messages (not ChatPromptTemplate) on purpose:
the analysis text contains characters like '{' '}' that template parsing would
misinterpret. Passing messages directly avoids that.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import IncidentState
from app.ai.models import get_chat_model
from app.core.config import settings
from app.core.guards import sanitize_for_prompt
from app.core.metrics import llm_calls_total
from app.rag.knowledge import retrieve_context


def format_analysis(analysis: dict) -> str:
    """Render the Phase 10 analysis dict into readable text for prompts."""
    lines = [
        f"Total log lines: {analysis.get('total_lines', 0)}",
        f"Level counts: {analysis.get('level_counts', {})}",
        f"Services involved: {', '.join(analysis.get('services', [])) or 'unknown'}",
        f"Error count: {analysis.get('error_count', 0)}",
    ]
    errors = analysis.get("error_messages", [])
    if errors:
        lines.append("Error messages:")
        lines.extend(f"  - {m}" for m in errors)
    correlations = analysis.get("correlation_groups", {})
    if correlations:
        lines.append("Correlated request flows:")
        for corr_id, msgs in correlations.items():
            lines.append(f"  [{corr_id}] " + " -> ".join(msgs))
    # Logs are UNTRUSTED input — sanitize before it reaches the LLM (Phase 21).
    return sanitize_for_prompt("\n".join(lines))


def _llm_text(system: str, user: str) -> str:
    """Run a single text completion against the local model."""
    llm_calls_total.inc()  # Prometheus metric (Phase 17)
    response = get_chat_model().invoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )
    return response.content.strip()


# === 1. Log Analyzer =========================================================
def log_analyzer_node(state: IncidentState) -> dict:
    analysis = format_analysis(state.get("analysis", {}))
    summary = _llm_text(
        "You are a senior SRE Log Analyzer. In 2-4 factual sentences, summarize "
        "what the logs show. State facts only, no speculation.",
        f"Incident log analysis:\n{analysis}\n\nSummarize what happened.",
    )
    return {"log_summary": summary}


# === 2. Monitoring ===========================================================
def monitoring_node(state: IncidentState) -> dict:
    analysis = format_analysis(state.get("analysis", {}))
    anomalies = _llm_text(
        "You are a Monitoring agent. Identify anomalies, error spikes, and which "
        "services are degraded. Be concise; use bullet points.",
        f"Analysis:\n{analysis}\n\nLog summary: {state.get('log_summary', '')}\n\n"
        "List the anomalies.",
    )
    return {"anomalies": anomalies}


# === RAG retrieval (Phase 15) ===============================================
def retrieval_node(state: IncidentState) -> dict:
    """Fetch relevant runbooks / past incidents from the vector store.

    RAG depends on local embeddings (Ollama), so it degrades gracefully when
    disabled or unavailable (e.g. in the cloud) — the agents still run.
    """
    if not settings.RAG_ENABLED:
        return {"retrieved_context": "(knowledge base disabled)"}
    try:
        query = f"{state.get('log_summary', '')} {state.get('anomalies', '')}"
        docs = retrieve_context(query, k=3)
        context = "\n\n".join(
            f"[{d.metadata.get('title', 'doc')}] {d.page_content}" for d in docs
        )
        return {"retrieved_context": context or "(no relevant knowledge found)"}
    except Exception:
        return {"retrieved_context": "(knowledge base unavailable)"}


# === 3. Root Cause (RAG-augmented) ==========================================
def root_cause_node(state: IncidentState) -> dict:
    root_cause = _llm_text(
        "You are a Root Cause Analysis expert. Use the reference runbooks/past "
        "incidents if relevant. State the single MOST LIKELY root cause and justify it.",
        f"Reference knowledge (runbooks / past incidents):\n"
        f"{state.get('retrieved_context', '')}\n\n"
        f"Log summary: {state.get('log_summary', '')}\n"
        f"Anomalies: {state.get('anomalies', '')}\n\n"
        "What is the most likely root cause?",
    )
    return {"root_cause": root_cause}


# === 4. Severity Assessment (structured output) ==============================
class SeverityVerdict(BaseModel):
    severity: int = Field(ge=1, le=4, description="1=critical .. 4=minor")
    reason: str = Field(description="short justification")


def severity_node(state: IncidentState) -> dict:
    llm_calls_total.inc()  # Prometheus metric (Phase 17)
    model = get_chat_model().with_structured_output(SeverityVerdict)
    verdict = model.invoke(
        [
            SystemMessage(
                content="You are an SRE triaging incidents. Assign severity: "
                "1=critical outage, 2=major degradation, 3=minor, 4=low."
            ),
            HumanMessage(
                content=f"Root cause: {state.get('root_cause', '')}\n"
                f"Anomalies: {state.get('anomalies', '')}\n\nAssign a severity."
            ),
        ]
    )
    return {"severity": verdict.severity, "severity_reason": verdict.reason}


# === 5. Fix Recommendation ===================================================
def fix_recommendation_node(state: IncidentState) -> dict:
    fixes = _llm_text(
        "You are an SRE recommending fixes. Use the reference runbooks if relevant. "
        "Give concrete, actionable, numbered fixes.",
        f"Reference knowledge:\n{state.get('retrieved_context', '')}\n\n"
        f"Root cause: {state.get('root_cause', '')}\n\nRecommend fixes.",
    )
    return {"recommended_fix": fixes}


# === 6. Recovery Planner =====================================================
def recovery_planner_node(state: IncidentState) -> dict:
    plan = _llm_text(
        "You are an incident commander. Give a clear, numbered step-by-step recovery "
        "plan to restore service NOW (mitigation first, then permanent fix).",
        f"Root cause: {state.get('root_cause', '')}\n"
        f"Recommended fixes: {state.get('recommended_fix', '')}\n\n"
        "Write the recovery plan.",
    )
    return {"recovery_plan": plan}


# === 7. Report Generator =====================================================
def report_generator_node(state: IncidentState) -> dict:
    report = _llm_text(
        "You are writing a concise, blameless post-mortem. Use sections: "
        "Summary, Impact, Root Cause, Resolution, Action Items.",
        f"Log summary: {state.get('log_summary', '')}\n"
        f"Anomalies: {state.get('anomalies', '')}\n"
        f"Root cause: {state.get('root_cause', '')}\n"
        f"Severity: SEV-{state.get('severity', '?')} ({state.get('severity_reason', '')})\n"
        f"Recommended fix: {state.get('recommended_fix', '')}\n"
        f"Recovery plan: {state.get('recovery_plan', '')}\n\n"
        "Write the post-mortem.",
    )
    analysis = state.get("analysis", {})
    confidence = 0.8 if analysis.get("error_count", 0) > 0 else 0.5
    return {"report": report, "confidence": confidence}
