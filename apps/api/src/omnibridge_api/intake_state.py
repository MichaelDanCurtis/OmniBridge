from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from threading import Lock

from pydantic import BaseModel

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


_REPO_ROOT = Path(__file__).resolve().parents[4]
_RELEASE1_FIXTURE_PATH = (
    _REPO_ROOT / "corridors" / "vmware-to-azure" / "fixtures" / "acme-small-estate.json"
)
_FIXED_RELEASE1_HEARTBEAT = "2026-05-10T12:00:00Z"


class CollectorStatus(StrEnum):
    NOT_DEPLOYED = "not_deployed"
    CONNECTED = "connected"


class DiscoveryRunStatus(StrEnum):
    NOT_STARTED = "not_started"
    COMPLETED = "completed"


class CollectorSnapshot(BaseModel):
    collector_id: str
    status: CollectorStatus
    vcenter: str
    last_heartbeat_at: str | None


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


class CollectorNotConnectedError(RuntimeError):
    pass


@dataclass
class _Release1IntakeState:
    collector_status: CollectorStatus = CollectorStatus.NOT_DEPLOYED
    last_heartbeat_at: str | None = None
    discovery_status: DiscoveryRunStatus = DiscoveryRunStatus.NOT_STARTED
    discovery_run_id: str | None = None
    compute_nodes: int = 0
    network_segments: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0


_state = _Release1IntakeState()
_state_lock = Lock()


def reset_release1_intake_state() -> None:
    with _state_lock:
        global _state
        _state = _Release1IntakeState()


def get_release1_intake_snapshot() -> IntakeSnapshot:
    with _state_lock:
        return _snapshot_from_state(_state)


def deploy_release1_collector() -> IntakeSnapshot:
    with _state_lock:
        _state.collector_status = CollectorStatus.CONNECTED
        _state.last_heartbeat_at = _FIXED_RELEASE1_HEARTBEAT
        return _snapshot_from_state(_state)


def record_release1_collector_heartbeat() -> IntakeSnapshot:
    with _state_lock:
        _state.collector_status = CollectorStatus.CONNECTED
        _state.last_heartbeat_at = _FIXED_RELEASE1_HEARTBEAT
        return _snapshot_from_state(_state)


def start_release1_discovery_run() -> IntakeSnapshot:
    with _state_lock:
        if _state.collector_status != CollectorStatus.CONNECTED:
            raise CollectorNotConnectedError(
                "Collector must be connected before discovery can run."
            )

        fixture = load_fixture(_RELEASE1_FIXTURE_PATH)
        graph = map_fixture_to_graph(fixture)
        _state.discovery_status = DiscoveryRunStatus.COMPLETED
        _state.discovery_run_id = "discovery-release1-demo-001"
        _state.compute_nodes = len(fixture.get("vms", []))
        _state.network_segments = len(fixture.get("networks", []))
        _state.graph_nodes = len(graph.nodes)
        _state.graph_edges = len(graph.edges)
        return _snapshot_from_state(_state)


def _snapshot_from_state(state: _Release1IntakeState) -> IntakeSnapshot:
    return IntakeSnapshot(
        project_id="project-acme-vmware-azure",
        collector=CollectorSnapshot(
            collector_id="collector-release1-demo",
            status=state.collector_status,
            vcenter="vcsa-prod-01",
            last_heartbeat_at=state.last_heartbeat_at,
        ),
        discovery=DiscoveryRunSnapshot(
            run_id=state.discovery_run_id,
            status=state.discovery_status,
            source="fixture",
            compute_nodes=state.compute_nodes,
            network_segments=state.network_segments,
            graph_nodes=state.graph_nodes,
            graph_edges=state.graph_edges,
            estimate_ready=state.discovery_status == DiscoveryRunStatus.COMPLETED,
        ),
    )
