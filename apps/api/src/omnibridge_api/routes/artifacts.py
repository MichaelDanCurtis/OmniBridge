from fastapi import APIRouter, Response

from omnibridge_blueprint_engine.artifacts import render_assessment_markdown


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/release1-assessment.md")
def release1_assessment_artifact() -> Response:
    markdown = render_assessment_markdown(
        project_name="ACME VMware-to-Azure Assessment",
        application_name="Claims Portal",
        blockers=1,
        estimate_usd=27250,
    )
    return Response(content=markdown, media_type="text/markdown")
