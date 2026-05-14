from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from omnibridge_api.intake_state import reset_release1_intake_state
from omnibridge_api.main import app


@pytest.fixture(autouse=True)
def release1_intake_state() -> Iterator[None]:
    reset_release1_intake_state()
    yield
    reset_release1_intake_state()


def test_latest_discovery_run_starts_with_collector_not_deployed() -> None:
    client = TestClient(app)

    response = client.get("/discovery-runs/release1-demo/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "project-release1-vmware-azure"
    assert payload["collector"] == {
        "collector_id": "collector-release1-demo",
        "status": "not_deployed",
        "vcenter": "vcsa-prod-01",
        "last_heartbeat_at": None,
        "version": None,
        "capabilities": [],
    }
    assert payload["discovery"] == {
        "run_id": None,
        "status": "not_started",
        "source": "fixture",
        "compute_nodes": 0,
        "network_segments": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "estimate_ready": False,
    }


def test_discovery_run_requires_connected_collector() -> None:
    client = TestClient(app)

    response = client.post("/discovery-runs/release1-demo/start")

    assert response.status_code == 409
    assert response.json()["detail"] == "Collector must be online before discovery can run."


def test_collector_registration_and_discovery_run_unlock_estimate_data() -> None:
    client = TestClient(app)

    bootstrap_response = client.post("/collectors/release1-demo/bootstrap")

    assert bootstrap_response.status_code == 200
    bootstrap = bootstrap_response.json()
    registration_token = bootstrap["registration"]["registration_token"]
    assert bootstrap["collector"]["status"] == "pending_registration"

    register_response = client.post(
        "/collectors/release1-demo/register",
        json={
            "collector_id": "collector-release1-demo",
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert register_response.status_code == 200
    registered = register_response.json()
    assert registered["collector"]["status"] == "online"
    assert registered["discovery"]["status"] == "not_started"
    assert registered["discovery"]["estimate_ready"] is False

    discovery_response = client.post("/discovery-runs/release1-demo/start")

    assert discovery_response.status_code == 200
    queued = discovery_response.json()
    assert queued["collector"]["status"] == "online"
    assert queued["discovery"] == {
        "run_id": "discovery-release1-demo-001",
        "status": "queued",
        "source": "fixture",
        "compute_nodes": 0,
        "network_segments": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "estimate_ready": False,
    }

    claim_response = client.post(
        "/collectors/collector-release1-demo/jobs/claim",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert claim_response.status_code == 200
    claim = claim_response.json()
    assert claim["job"] == {
        "job_id": "discovery-release1-demo-001",
        "job_type": "discovery",
        "status": "running",
        "parameters": {"source": "fixture"},
    }

    complete_response = client.post(
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

    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["collector"]["status"] == "online"
    assert completed["discovery"] == {
        "run_id": "discovery-release1-demo-001",
        "status": "completed",
        "source": "fixture",
        "compute_nodes": 3,
        "network_segments": 3,
        "graph_nodes": 12,
        "graph_edges": 13,
        "estimate_ready": True,
    }


def test_online_collector_bootstrap_attempt_preserves_completed_discovery() -> None:
    client = TestClient(app)
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

    response = client.post("/collectors/release1-demo/bootstrap")

    assert response.status_code == 409
    latest = client.get("/discovery-runs/release1-demo/latest").json()
    assert latest["collector"]["status"] == "online"
    assert latest["discovery"]["status"] == "queued"
    assert latest["discovery"]["estimate_ready"] is False
