from omnibridge_blueprint_engine.artifacts import render_assessment_markdown


def test_render_assessment_markdown_contains_project_and_decisions() -> None:
    markdown = render_assessment_markdown(
        project_name="ACME VMware-to-Azure Assessment",
        application_name="Claims Portal",
        blockers=1,
        estimate_usd=27250,
    )

    assert "# ACME VMware-to-Azure Assessment" in markdown
    assert "Claims Portal" in markdown
    assert "1 blocker" in markdown
    assert "$27,250" in markdown
