from fastapi import APIRouter


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/summary")
def graph_summary() -> dict[str, int]:
    return {
        "compute_nodes": 3,
        "network_segments": 3,
        "applications": 1,
        "readiness_findings": 1,
    }
