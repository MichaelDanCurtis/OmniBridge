from fastapi import APIRouter, HTTPException

from omnibridge_api.intake_state import (
    CollectorAlreadyOnlineError,
    CollectorHeartbeatRequest,
    CollectorJobCompletionRequest,
    CollectorNotFoundError,
    CollectorNotConnectedError,
    CollectorRegistrationRequest,
    InvalidRegistrationTokenError,
    RunNotFoundError,
    RunTransitionError,
    bootstrap_release1_collector,
    claim_release1_collector_job,
    complete_release1_collector_job,
    get_release1_intake_snapshot,
    record_release1_collector_heartbeat,
    register_release1_collector,
    start_release1_discovery_run,
)


collectors_router = APIRouter(prefix="/collectors", tags=["intake"])
discovery_runs_router = APIRouter(prefix="/discovery-runs", tags=["intake"])


@collectors_router.post("/release1-demo/bootstrap")
def bootstrap_release1_demo_collector() -> dict[str, object]:
    try:
        bootstrap = bootstrap_release1_collector()
    except CollectorAlreadyOnlineError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return bootstrap.model_dump(mode="json")


@collectors_router.post("/release1-demo/deploy")
def deploy_release1_demo_collector() -> dict[str, object]:
    try:
        bootstrap = bootstrap_release1_collector()
    except CollectorAlreadyOnlineError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return bootstrap.model_dump(mode="json")


@collectors_router.post("/release1-demo/register")
def register_release1_demo_collector(
    request: CollectorRegistrationRequest,
) -> dict[str, object]:
    try:
        snapshot = register_release1_collector(request)
    except CollectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collector was not bootstrapped.") from exc
    except InvalidRegistrationTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return snapshot.model_dump(mode="json")


@collectors_router.post("/{collector_id}/heartbeat")
def heartbeat_collector(
    collector_id: str,
    request: CollectorHeartbeatRequest,
) -> dict[str, object]:
    try:
        snapshot = record_release1_collector_heartbeat(
            collector_id=collector_id,
            request=request,
        )
    except CollectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collector was not bootstrapped.") from exc
    except InvalidRegistrationTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return snapshot.model_dump(mode="json")


@collectors_router.post("/{collector_id}/jobs/claim")
def claim_collector_job(
    collector_id: str,
    request: CollectorHeartbeatRequest,
) -> dict[str, object]:
    try:
        claim = claim_release1_collector_job(
            collector_id=collector_id,
            request=request,
        )
    except CollectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collector was not bootstrapped.") from exc
    except InvalidRegistrationTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return claim.model_dump(mode="json")


@collectors_router.post("/{collector_id}/jobs/{job_id}/complete")
def complete_collector_job(
    collector_id: str,
    job_id: str,
    request: CollectorJobCompletionRequest,
) -> dict[str, object]:
    try:
        snapshot = complete_release1_collector_job(
            collector_id=collector_id,
            job_id=job_id,
            request=request,
        )
    except CollectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collector was not bootstrapped.") from exc
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collector job was not found.") from exc
    except RunTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail="Collector job is not running for this collector.",
        ) from exc
    except InvalidRegistrationTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return snapshot.model_dump(mode="json")


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
