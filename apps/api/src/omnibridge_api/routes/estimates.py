from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/estimates", tags=["estimates"])


@router.get("/release1-demo")
def release1_demo_estimate() -> dict[str, object]:
    return build_release1_demo().estimate.model_dump()
