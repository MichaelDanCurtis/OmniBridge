from enum import StrEnum
from pathlib import Path
import secrets

from pydantic import BaseModel

from omnibridge_api.control_plane_store import (
    CollectorNotFoundError,
    ControlPlaneStore,
    InvalidRegistrationTokenError,
    StoredCollector,
    default_store,
)
from omnibridge_api.settings import settings
from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


_REPO_ROOT = Path(__file__).resolve().parents[4]
_RELEASE1_FIXTURE_PATH = (
    _REPO_ROOT / "corridors" / "vmware-to-azure" / "fixtures" / "acme-small-estate.json"
)
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
    COMPLETED = "completed"


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

    fixture = load_fixture(_RELEASE1_FIXTURE_PATH)
    graph = map_fixture_to_graph(fixture)
    result = {
        "source": "fixture",
        "compute_nodes": len(fixture.get("vms", [])),
        "network_segments": len(fixture.get("networks", [])),
        "graph_nodes": len(graph.nodes),
        "graph_edges": len(graph.edges),
        "estimate_ready": True,
    }
    store.record_run(
        run_id="discovery-release1-demo-001",
        project_id=_RELEASE1_PROJECT_ID,
        run_type="discovery",
        status="completed",
        collector_id=collector.collector_id,
        result=result,
    )
    return _snapshot_from_store(store, collector=collector)


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
            status=(
                DiscoveryRunStatus.COMPLETED
                if discovery_run and discovery_run.status == "completed"
                else DiscoveryRunStatus.NOT_STARTED
            ),
            source=str(discovery_result.get("source", "fixture")),
            compute_nodes=int(discovery_result.get("compute_nodes", 0)),
            network_segments=int(discovery_result.get("network_segments", 0)),
            graph_nodes=int(discovery_result.get("graph_nodes", 0)),
            graph_edges=int(discovery_result.get("graph_edges", 0)),
            estimate_ready=bool(discovery_result.get("estimate_ready", False)),
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


__all__ = [
    "CollectorAlreadyOnlineError",
    "CollectorHeartbeatRequest",
    "CollectorNotConnectedError",
    "CollectorRegistrationRequest",
    "InvalidRegistrationTokenError",
    "CollectorNotFoundError",
    "bootstrap_release1_collector",
    "get_release1_intake_snapshot",
    "record_release1_collector_heartbeat",
    "register_release1_collector",
    "reset_release1_intake_state",
    "start_release1_discovery_run",
]
