from typing import Any

from fastapi import APIRouter

from omnibridge_api.release1_demo import build_release1_demo

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/release1-demo")
def release1_demo_validation() -> dict[str, Any]:
    return build_release1_demo().validation_evidence.model_dump(mode="json")
