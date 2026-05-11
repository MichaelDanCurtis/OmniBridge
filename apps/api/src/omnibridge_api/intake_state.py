from enum import StrEnum
import secrets

from pydantic import BaseModel

from omnibridge_api.control_plane_store import (
    CollectorNotFoundError,
    ControlPlaneStore,
    InvalidRegistrationTokenError,
    RunNotFoundError,
    RunTransitionError,
    StoredCollector,
    StoredRun,
    default_store,
)
from omnibridge_api.settings import settings


_RELEASE1_PROJECT_ID = "project-acme-vmware-azure"
_RELEASE1_COLLECTOR_ID = "collector-release1-demo"
_RELEASE1_VCENTER = "vcsa-prod-01"


class CollectorStatus(StrEnum):
    NOT_DEPLOYED = "not_deployed"
    PENDING_REGISTRATION = "pending_registration"
    ONLINE = "online"
    OFFLINE = "offline"
    REVOKED = "revoked"


class DiscoveryRunStatus(StrEnum):
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CollectorSnapshot(BaseModel):
    collector_id: str
    status: CollectorStatus
    vcenter: str
    last_heartbeat_at: str | None
    version: str | None = None
    capabilities: list[str] = []


class DiscoveryRunSnapshot(BaseModel):
    run_id: str | None
    status: DiscoveryRunStatus
    source: str
    compute_nodes: int
    network_segments: int
    graph_nodes: int
    graph_edges: int
    estimate_ready: bool


class IntakeSnapshot(BaseModel):
    project_id: str
    collector: CollectorSnapshot
    discovery: DiscoveryRunSnapshot


class CollectorRegistrationPackage(BaseModel):
    collector_id: str
    registration_token: str
    api_url: str
    install_command: str


class CollectorBootstrapResponse(BaseModel):
    project_id: str
    collector: CollectorSnapshot
    registration: CollectorRegistrationPackage


class CollectorRegistrationRequest(BaseModel):
    collector_id: str
    registration_token: str
    version: str
    capabilities: list[str]


class CollectorHeartbeatRequest(BaseModel):
    registration_token: str
    version: str
    capabilities: list[str]


class CollectorJob(BaseModel):
    job_id: str
    job_type: str
    status: str
    parameters: dict[str, object]


class CollectorJobClaimResponse(BaseModel):
    project_id: str
    collector: CollectorSnapshot
    job: CollectorJob | None


class CollectorJobCompletionRequest(CollectorHeartbeatRequest):
    result: dict[str, object]


class CollectorNotConnectedError(RuntimeError):
    pass


class CollectorAlreadyOnlineError(RuntimeError):
    pass


def reset_release1_intake_state() -> None:
    default_store().reset()


def get_release1_intake_snapshot() -> IntakeSnapshot:
    return _snapshot_from_store(default_store())


def bootstrap_release1_collector() -> CollectorBootstrapResponse:
    store = default_store()
    existing = store.get_collector(_RELEASE1_COLLECTOR_ID)
    if existing is not None and existing.status == CollectorStatus.ONLINE:
        raise CollectorAlreadyOnlineError(
            "Collector is already online. Revoke or rotate it explicitly before bootstrapping."
        )

    registration_token = secrets.token_urlsafe(32)
    stored = store.bootstrap_collector(
        project_id=_RELEASE1_PROJECT_ID,
        collector_id=_RELEASE1_COLLECTOR_ID,
        vcenter=_RELEASE1_VCENTER,
        registration_token=registration_token,
    )
    registration = CollectorRegistrationPackage(
        collector_id=_RELEASE1_COLLECTOR_ID,
        registration_token=registration_token,
        api_url=settings.api_public_url,
        install_command=(
            "omnibridge-collector register "
            f"--api-url {settings.api_public_url} "
            f"--collector-id {_RELEASE1_COLLECTOR_ID} "
            f"--registration-token {registration_token}"
        ),
    )
    return CollectorBootstrapResponse(
        project_id=_RELEASE1_PROJECT_ID,
        collector=_collector_snapshot(stored),
        registration=registration,
    )


def register_release1_collector(request: CollectorRegistrationRequest) -> IntakeSnapshot:
    stored = default_store().register_collector(
        collector_id=request.collector_id,
        registration_token=request.registration_token,
        version=request.version,
        capabilities=request.capabilities,
    )
    return _snapshot_from_store(default_store(), collector=stored)


def record_release1_collector_heartbeat(
    collector_id: str,
    request: CollectorHeartbeatRequest,
) -> IntakeSnapshot:
    stored = default_store().record_collector_heartbeat(
        collector_id=collector_id,
        registration_token=request.registration_token,
        version=request.version,
        capabilities=request.capabilities,
    )
    return _snapshot_from_store(default_store(), collector=stored)


def start_release1_discovery_run() -> IntakeSnapshot:
    store = default_store()
    collector = store.get_collector(_RELEASE1_COLLECTOR_ID)
    if collector is None or collector.status != CollectorStatus.ONLINE:
        raise CollectorNotConnectedError("Collector must be online before discovery can run.")

    store.record_run(
        run_id="discovery-release1-demo-001",
        project_id=_RELEASE1_PROJECT_ID,
        run_type="discovery",
        status=DiscoveryRunStatus.QUEUED,
        collector_id=None,
        result={
            "source": "fixture",
            "estimate_ready": False,
        },
    )
    return _snapshot_from_store(store, collector=collector)


def claim_release1_collector_job(
    collector_id: str,
    request: CollectorHeartbeatRequest,
) -> CollectorJobClaimResponse:
    store = default_store()
    run = store.claim_next_run(
        project_id=_RELEASE1_PROJECT_ID,
        collector_id=collector_id,
        registration_token=request.registration_token,
        version=request.version,
        capabilities=request.capabilities,
    )
    collector = store.get_collector(collector_id)
    if collector is None:
        raise CollectorNotFoundError(collector_id)

    return CollectorJobClaimResponse(
        project_id=_RELEASE1_PROJECT_ID,
        collector=_collector_snapshot(collector),
        job=_job_from_run(run) if run is not None else None,
    )


def complete_release1_collector_job(
    collector_id: str,
    job_id: str,
    request: CollectorJobCompletionRequest,
) -> IntakeSnapshot:
    store = default_store()
    collector = store.get_collector(collector_id)
    if collector is None:
        raise CollectorNotFoundError(collector_id)

    store.complete_run(
        run_id=job_id,
        collector_id=collector_id,
        registration_token=request.registration_token,
        version=request.version,
        capabilities=request.capabilities,
        result=dict(request.result),
    )
    collector = store.get_collector(collector_id)
    if collector is None:
        raise CollectorNotFoundError(collector_id)

    return _snapshot_from_store(store, collector=collector)


def release1_fixture_discovery_result() -> dict[str, object]:
    return {
        "source": "fixture",
        "compute_nodes": 3,
        "network_segments": 3,
        "graph_nodes": 12,
        "graph_edges": 13,
        "estimate_ready": True,
    }


def _snapshot_from_store(
    store: ControlPlaneStore,
    collector: StoredCollector | None = None,
) -> IntakeSnapshot:
    stored_collector = collector or store.get_collector(_RELEASE1_COLLECTOR_ID)
    discovery_run = store.get_run("discovery-release1-demo-001")
    discovery_result = discovery_run.result if discovery_run else {}
    return IntakeSnapshot(
        project_id=_RELEASE1_PROJECT_ID,
        collector=(
            _collector_snapshot(stored_collector)
            if stored_collector is not None
            else _default_collector_snapshot()
        ),
        discovery=DiscoveryRunSnapshot(
            run_id=discovery_run.run_id if discovery_run else None,
            status=_discovery_status(discovery_run),
            source=str(discovery_result.get("source", "fixture")),
            compute_nodes=_completed_int(discovery_run, discovery_result, "compute_nodes"),
            network_segments=_completed_int(discovery_run, discovery_result, "network_segments"),
            graph_nodes=_completed_int(discovery_run, discovery_result, "graph_nodes"),
            graph_edges=_completed_int(discovery_run, discovery_result, "graph_edges"),
            estimate_ready=(
                discovery_run is not None
                and discovery_run.status == DiscoveryRunStatus.COMPLETED
                and bool(discovery_result.get("estimate_ready", False))
            ),
        ),
    )


def _collector_snapshot(stored: StoredCollector) -> CollectorSnapshot:
    return CollectorSnapshot(
        collector_id=stored.collector_id,
        status=CollectorStatus(stored.status),
        vcenter=stored.vcenter,
        last_heartbeat_at=stored.last_heartbeat_at,
        version=stored.version,
        capabilities=stored.capabilities,
    )


def _default_collector_snapshot() -> CollectorSnapshot:
    return CollectorSnapshot(
        collector_id=_RELEASE1_COLLECTOR_ID,
        status=CollectorStatus.NOT_DEPLOYED,
        vcenter=_RELEASE1_VCENTER,
        last_heartbeat_at=None,
    )


def _job_from_run(run: StoredRun) -> CollectorJob:
    return CollectorJob(
        job_id=run.run_id,
        job_type=run.run_type,
        status=run.status,
        parameters={"source": str(run.result.get("source", "fixture"))},
    )


def _discovery_status(run: StoredRun | None) -> DiscoveryRunStatus:
    if run is None:
        return DiscoveryRunStatus.NOT_STARTED
    return DiscoveryRunStatus(run.status)


def _completed_int(run: StoredRun | None, result: dict[str, object], key: str) -> int:
    if run is None or run.status != DiscoveryRunStatus.COMPLETED:
        return 0
    return int(result.get(key, 0))


__all__ = [
    "CollectorAlreadyOnlineError",
    "CollectorHeartbeatRequest",
    "CollectorJobCompletionRequest",
    "CollectorNotConnectedError",
    "CollectorRegistrationRequest",
    "InvalidRegistrationTokenError",
    "CollectorNotFoundError",
    "RunNotFoundError",
    "RunTransitionError",
    "bootstrap_release1_collector",
    "claim_release1_collector_job",
    "complete_release1_collector_job",
    "get_release1_intake_snapshot",
    "record_release1_collector_heartbeat",
    "register_release1_collector",
    "release1_fixture_discovery_result",
    "reset_release1_intake_state",
    "start_release1_discovery_run",
]
