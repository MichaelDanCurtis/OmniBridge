from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from omnibridge_agent_tools.graph_knowledge import GraphKnowledgeTools
from omnibridge_agent_tools.models import AnalysisResult, GraphTopologyContext


class AnalysisState(TypedDict):
    application_name: str
    compute_nodes: list[str]
    blocker_count: int
    warning_count: int
    analysis_source: str
    topology_context: GraphTopologyContext | None
    result: AnalysisResult | None


def _summarize(state: AnalysisState) -> AnalysisState:
    application_name = state["application_name"]
    compute_nodes = state["compute_nodes"]
    blocker_count = state["blocker_count"]
    warning_count = state["warning_count"]
    topology_context = state["topology_context"]

    if topology_context is not None:
        decision_points = [
            *[
                f"Review graph evidence: {edge}"
                for edge in topology_context.evidence_edges[:3]
            ],
            "Confirm graph-derived dependencies before blueprint approval.",
        ]
        summary = f"{application_name} graph analysis: {topology_context.summary}"
    else:
        decision_points = [
            "Confirm whether claims-db-01 snapshot can be removed.",
            "Confirm Azure subnet mapping for database tier.",
        ]
        summary = (
            f"{application_name} contains {len(compute_nodes)} compute nodes with "
            f"{blocker_count} blocker(s) and {warning_count} warning(s)."
        )

    return {
        **state,
        "result": AnalysisResult(
            summary=summary,
            requires_consultant_review=blocker_count > 0 or warning_count > 0,
            decision_points=decision_points,
            analysis_source=state["analysis_source"],
            graph_context_summary=topology_context.summary if topology_context else None,
            graph_evidence_edges=topology_context.evidence_edges if topology_context else [],
        ),
    }


def build_analysis_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("summarize", _summarize)
    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


def run_fixture_analysis(
    compute_nodes: list[str],
    blocker_count: int,
    warning_count: int,
) -> AnalysisResult:
    graph = build_analysis_graph()
    final_state = graph.invoke(
        {
            "application_name": "Claims Portal",
            "compute_nodes": compute_nodes,
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "analysis_source": "fixture",
            "topology_context": None,
            "result": None,
        }
    )
    result = final_state["result"]
    if result is None:
        raise RuntimeError("Analysis graph did not produce a result.")
    return result


def run_graph_grounded_analysis(
    application_name: str,
    project_id: str,
    tenant_id: str,
    graph_tools: GraphKnowledgeTools,
    blocker_count: int,
    warning_count: int,
) -> AnalysisResult:
    graph = build_analysis_graph()
    topology_context = graph_tools.get_project_topology_context(
        project_id=project_id,
        tenant_id=tenant_id,
        edge_limit=100,
    )
    final_state = graph.invoke(
        {
            "application_name": application_name,
            "compute_nodes": [],
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "analysis_source": "graph",
            "topology_context": topology_context,
            "result": None,
        }
    )
    result = final_state["result"]
    if result is None:
        raise RuntimeError("Graph-grounded analysis did not produce a result.")
    return result
