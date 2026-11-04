from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from omnibridge_api.intake_state import reset_release1_intake_state
from omnibridge_api.main import app
from omnibridge_api.routes import approvals as approvals_routes
from omnibridge_api.routes import migration_waves as migration_waves_routes
from omnibridge_workflow_engine.models import ApprovalLedger


@pytest.fixture(autouse=True)
def release1_workflow_state() -> Iterator[None]:
    reset_release1_intake_state()
    approvals_routes._release1_ledger = ApprovalLedger.seed_release1()
    if hasattr(migration_waves_routes, "reset_release1_migration_wave_state"):
        migration_waves_routes.reset_release1_migration_wave_state()
    yield
    reset_release1_intake_state()
    approvals_routes._release1_ledger = ApprovalLedger.seed_release1()
    if hasattr(migration_waves_routes, "reset_release1_migration_wave_state"):
        migration_waves_routes.reset_release1_migration_wave_state()


def _complete_discovery(client: TestClient) -> None:
    bootstrap = client.post("/collectors/release1-demo/bootstrap").json()
    registration_token = bootstrap["registration"]["registration_token"]
    client.post(
        "/collectors/release1-demo/register",
        json={
            "collector_id": "collector-release1-demo",
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )
    client.post("/discovery-runs/release1-demo/start")
    client.post(
        "/collectors/collector-release1-demo/jobs/claim",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )
    client.post(
        "/collectors/collector-release1-demo/jobs/discovery-release1-demo-001/complete",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
            "result": {
                "source": "fixture",
                "compute_nodes": 3,
                "network_segments": 3,
                "graph_nodes": 12,
                "graph_edges": 13,
                "estimate_ready": True,
            },
        },
    )


def _approve_estimate(client: TestClient) -> None:
    client.post(
        "/approvals/release1-demo/commercial_estimate_approval/approve",
        json={
            "actor": "consultant@example.com",
            "reason": "Customer approved the estimate.",
        },
    )


def test_current_migration_wave_starts_empty() -> None:
    client = TestClient(app)

    response = client.get("/migration-waves/release1-demo/current")

    assert response.status_code == 200
    assert response.json() == {
        "wave_id": None,
        "status": "not_created",
        "selected_compute_nodes": [],
        "execution_backend": "azure-migrate",
        "operation_count": 0,
        "approval_gates": [],
        "ready_count": 0,
        "blocked_count": 0,
        "blockers": [],
        "next_action": "Create a migration wave.",
    }


def test_migration_wave_requires_discovery_and_estimate_approval() -> None:
    client = TestClient(app)

    before_discovery = client.post(
        "/migration-waves/release1-demo",
        json={"compute_nodes": ["claims-web-01"]},
    )

    assert before_discovery.status_code == 409
    assert before_discovery.json()["detail"] == (
        "Discovery must complete before a migration wave can be created."
    )

    _complete_discovery(client)
    before_approval = client.post(
        "/migration-waves/release1-demo",
        json={"compute_nodes": ["claims-web-01"]},
    )

    assert before_approval.status_code == 409
    assert before_approval.json()["detail"] == (
        "Commercial estimate must be approved before creating a migration wave."
    )


def test_create_migration_wave_returns_execution_ready_scope_after_approval() -> None:
    client = TestClient(app)
    _complete_discovery(client)
    _approve_estimate(client)

    response = client.post(
        "/migration-waves/release1-demo",
        json={"compute_nodes": ["claims-web-01", "claims-db-01"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["wave_id"] == "wave-001"
    assert payload["status"] == "ready_for_test_migration"
    assert payload["selected_compute_nodes"] == ["claims-web-01", "claims-db-01"]
    assert payload["execution_backend"] == "azure-migrate"
    assert payload["operation_count"] == 6
    assert payload["approval_gates"] == [
        "test_migration_approval",
        "source_shutdown_approval",
        "cutover_approval",
    ]
    assert payload["ready_count"] == 1
    assert payload["blocked_count"] == 1
    assert payload["blockers"] == [
        {
            "name": "claims-db-01",
            "readiness": "Blocked",
            "message": "claims-db-01 has one or more VMware snapshots.",
        }
    ]
    assert payload["next_action"] == "Resolve blockers before test migration."

    current_response = client.get("/migration-waves/release1-demo/current")

    assert current_response.status_code == 200
    assert current_response.json() == payload


def test_create_migration_wave_rejects_unknown_compute_nodes() -> None:
    client = TestClient(app)
    _complete_discovery(client)
    _approve_estimate(client)

    response = client.post(
        "/migration-waves/release1-demo",
        json={"compute_nodes": ["not-a-real-vm"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown compute nodes: not-a-real-vm"
