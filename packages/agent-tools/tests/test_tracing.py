from omnibridge_agent_tools.models import AnalysisResult
from omnibridge_agent_tools.tracing import build_trace_metadata


def test_build_trace_metadata_contains_project_and_agent() -> None:
    result = AnalysisResult(
        summary="Claims Portal contains 3 compute nodes.",
        requires_consultant_review=True,
        decision_points=["Confirm database subnet mapping."],
    )

    metadata = build_trace_metadata(
        project_id="project-acme-vmware-azure",
        agent_name="release1-analysis-agent",
        result=result,
    )

    assert metadata["project_id"] == "project-acme-vmware-azure"
    assert metadata["agent_name"] == "release1-analysis-agent"
    assert metadata["requires_consultant_review"] is True
