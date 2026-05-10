from fastapi import APIRouter

from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/release1-demo")
def release1_demo_analysis() -> dict[str, object]:
    return run_fixture_analysis(
        compute_nodes=["claims-web-01", "claims-api-01", "claims-db-01"],
        blocker_count=1,
        warning_count=1,
    ).model_dump()
