from fastapi import APIRouter, HTTPException

from omnibridge_api.intake_state import (
    CollectorNotConnectedError,
    deploy_release1_collector,
    get_release1_intake_snapshot,
    record_release1_collector_heartbeat,
    start_release1_discovery_run,
)


collectors_router = APIRouter(prefix="/collectors", tags=["intake"])
discovery_runs_router = APIRouter(prefix="/discovery-runs", tags=["intake"])


@collectors_router.post("/release1-demo/deploy")
def deploy_release1_demo_collector() -> dict[str, object]:
    return deploy_release1_collector().model_dump(mode="json")


@collectors_router.post("/release1-demo/heartbeat")
def heartbeat_release1_demo_collector() -> dict[str, object]:
    return record_release1_collector_heartbeat().model_dump(mode="json")


@discovery_runs_router.get("/release1-demo/latest")
def latest_release1_demo_discovery_run() -> dict[str, object]:
    return get_release1_intake_snapshot().model_dump(mode="json")


@discovery_runs_router.post("/release1-demo/start")
def start_release1_demo_discovery_run() -> dict[str, object]:
    try:
        snapshot = start_release1_discovery_run()
    except CollectorNotConnectedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return snapshot.model_dump(mode="json")
