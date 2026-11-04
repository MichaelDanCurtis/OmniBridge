from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/summary")
def graph_summary() -> dict[str, int]:
    return build_release1_demo().graph_summary
