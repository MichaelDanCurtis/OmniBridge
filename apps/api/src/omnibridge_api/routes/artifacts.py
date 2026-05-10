from fastapi import APIRouter, Response

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/release1-assessment.md")
def release1_assessment_artifact() -> Response:
    return Response(
        content=build_release1_demo().assessment_markdown,
        media_type="text/markdown",
    )
