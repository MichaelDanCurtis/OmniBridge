from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/blueprints", tags=["blueprints"])


@router.get("/release1-demo")
def release1_demo_blueprint() -> dict[str, object]:
    return build_release1_demo().blueprint.model_dump(mode="json")
