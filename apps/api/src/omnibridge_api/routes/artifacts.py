from fastapi import APIRouter, Response

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/release1-assessment.md")
def release1_assessment_artifact() -> Response:
    return Response(
        content=build_release1_demo().assessment_markdown,
        media_type="text/markdown",
    )


@router.get("/release1-blueprint.yaml")
def release1_blueprint_artifact() -> Response:
    return Response(
        content=build_release1_demo().blueprint_yaml,
        media_type="application/yaml",
    )


@router.get("/release1-runbook.md")
def release1_runbook_artifact() -> Response:
    return Response(
        content=build_release1_demo().runbook_markdown,
        media_type="text/markdown",
    )
