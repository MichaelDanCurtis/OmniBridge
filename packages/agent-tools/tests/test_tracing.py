from omnibridge_agent_tools.models import AnalysisResult
from omnibridge_agent_tools.tracing import (
    AgentUsageRecord,
    build_trace_metadata,
    reconcile_agent_usage,
)


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


def test_reconcile_agent_usage_calculates_token_variance_and_charges() -> None:
    usage = AgentUsageRecord(
        project_id="project-acme-vmware-azure",
        agent_name="release1-analysis-agent",
        trace_id="trace-001",
        estimated_tokens=9_000_000,
        actual_input_tokens=450_000,
        actual_output_tokens=50_000,
        rate_per_1k_tokens_usd=0.20,
    )

    charge = reconcile_agent_usage(usage)

    assert charge.actual_tokens == 500_000
    assert charge.estimated_charge_usd == 1800.0
    assert charge.actual_charge_usd == 100.0
    assert charge.token_variance == -8_500_000


def test_build_trace_metadata_can_embed_langfuse_usage_payload() -> None:
    result = AnalysisResult(
        summary="Claims Portal contains 3 compute nodes.",
        requires_consultant_review=True,
        decision_points=["Confirm database subnet mapping."],
    )
    usage = AgentUsageRecord(
        project_id="project-acme-vmware-azure",
        agent_name="release1-analysis-agent",
        trace_id="trace-001",
        estimated_tokens=9_000_000,
        actual_input_tokens=450_000,
        actual_output_tokens=50_000,
        rate_per_1k_tokens_usd=0.20,
    )

    metadata = build_trace_metadata(
        project_id="project-acme-vmware-azure",
        agent_name="release1-analysis-agent",
        result=result,
        usage=usage,
    )

    assert metadata["langfuse_trace_id"] == "trace-001"
    assert metadata["estimated_agent_tokens"] == 9_000_000
    assert metadata["actual_agent_tokens"] == 500_000
    assert metadata["actual_agent_usage_charge_usd"] == 100.0
