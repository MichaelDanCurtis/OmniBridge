from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/execution-plans", tags=["execution-plans"])


@router.get("/release1-demo")
def release1_demo_execution_plan() -> dict[str, object]:
    return build_release1_demo().execution_plan.model_dump(mode="json")
