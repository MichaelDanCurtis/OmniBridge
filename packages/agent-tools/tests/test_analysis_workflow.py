from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis


def test_fixture_analysis_returns_consultant_summary() -> None:
    result = run_fixture_analysis(
        compute_nodes=["claims-web-01", "claims-api-01", "claims-db-01"],
        blocker_count=1,
        warning_count=1,
    )

    assert result.summary.startswith("Claims Portal")
    assert result.requires_consultant_review is True
