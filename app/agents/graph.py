"""Builds the multi-agent incident-analysis graph (Phase 13 wiring + Phase 14 agents).

The 7 nodes are now REAL LLM-powered agents (see app/agents/nodes.py). The
incident flows START -> log_analyzer -> ... -> report_generator -> END, with each
agent reading and extending the shared IncidentState.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    fix_recommendation_node,
    log_analyzer_node,
    monitoring_node,
    recovery_planner_node,
    report_generator_node,
    retrieval_node,
    root_cause_node,
    severity_node,
)
from app.agents.state import IncidentState


def build_incident_graph():
    """Construct and compile the incident-analysis graph."""
    graph = StateGraph(IncidentState)

    graph.add_node("log_analyzer", log_analyzer_node)
    graph.add_node("monitoring", monitoring_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("severity", severity_node)
    graph.add_node("fix_recommendation", fix_recommendation_node)
    graph.add_node("recovery_planner", recovery_planner_node)
    graph.add_node("report_generator", report_generator_node)

    graph.add_edge(START, "log_analyzer")
    graph.add_edge("log_analyzer", "monitoring")
    graph.add_edge("monitoring", "retrieval")
    graph.add_edge("retrieval", "root_cause")
    graph.add_edge("root_cause", "severity")
    graph.add_edge("severity", "fix_recommendation")
    graph.add_edge("fix_recommendation", "recovery_planner")
    graph.add_edge("recovery_planner", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()


# A single compiled instance the rest of the app imports and reuses.
incident_graph = build_incident_graph()
