def render_assessment_markdown(
    project_name: str,
    application_name: str,
    blockers: int,
    estimate_usd: int,
) -> str:
    return "\n".join(
        [
            f"# {project_name}",
            "",
            "## Application",
            application_name,
            "",
            "## Readiness",
            f"{blockers} blocker requires consultant review.",
            "",
            "## Estimate",
            f"${estimate_usd:,} project fee before usage overage.",
        ]
    )
