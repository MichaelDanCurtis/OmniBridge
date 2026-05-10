from omnibridge_agent_tools.models import AnalysisResult


def build_trace_metadata(
    project_id: str,
    agent_name: str,
    result: AnalysisResult,
) -> dict[str, object]:
    return {
        "project_id": project_id,
        "agent_name": agent_name,
        "requires_consultant_review": result.requires_consultant_review,
        "decision_point_count": len(result.decision_points),
    }
