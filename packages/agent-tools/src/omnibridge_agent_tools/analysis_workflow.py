from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from omnibridge_agent_tools.models import AnalysisResult


class AnalysisState(TypedDict):
    compute_nodes: list[str]
    blocker_count: int
    warning_count: int
    result: AnalysisResult | None


def _summarize(state: AnalysisState) -> AnalysisState:
    compute_nodes = state["compute_nodes"]
    blocker_count = state["blocker_count"]
    warning_count = state["warning_count"]

    return {
        **state,
        "result": AnalysisResult(
            summary=(
                f"Claims Portal contains {len(compute_nodes)} compute nodes with "
                f"{blocker_count} blocker(s) and {warning_count} warning(s)."
            ),
            requires_consultant_review=blocker_count > 0 or warning_count > 0,
            decision_points=[
                "Confirm whether claims-db-01 snapshot can be removed.",
                "Confirm Azure subnet mapping for database tier.",
            ],
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
            "compute_nodes": compute_nodes,
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "result": None,
        }
    )
    result = final_state["result"]
    if result is None:
        raise RuntimeError("Analysis graph did not produce a result.")
    return result
