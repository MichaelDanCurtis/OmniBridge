from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/release1-demo")
def release1_demo_workspace() -> dict[str, object]:
    return build_release1_demo().workspace
