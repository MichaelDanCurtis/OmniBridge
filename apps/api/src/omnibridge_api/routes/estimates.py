from fastapi import APIRouter

from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure


router = APIRouter(prefix="/estimates", tags=["estimates"])


@router.get("/release1-demo")
def release1_demo_estimate() -> dict[str, object]:
    return estimate_vmware_to_azure(
        compute_nodes=3,
        storage_gb=1280,
        network_segments=3,
        blocker_count=1,
        warning_count=1,
    ).model_dump()
