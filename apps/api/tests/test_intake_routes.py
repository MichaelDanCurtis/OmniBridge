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
    assert payload["project_id"] == "project-acme-vmware-azure"
    assert payload["collector"] == {
        "collector_id": "collector-release1-demo",
        "status": "not_deployed",
        "vcenter": "vcsa-prod-01",
        "last_heartbeat_at": None,
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
    assert response.json()["detail"] == "Collector must be connected before discovery can run."


def test_collector_deploy_and_discovery_run_unlock_estimate_data() -> None:
    client = TestClient(app)

    deploy_response = client.post("/collectors/release1-demo/deploy")

    assert deploy_response.status_code == 200
    deployed = deploy_response.json()
    assert deployed["collector"]["status"] == "connected"
    assert deployed["collector"]["last_heartbeat_at"] == "2026-05-10T12:00:00Z"
    assert deployed["discovery"]["status"] == "not_started"
    assert deployed["discovery"]["estimate_ready"] is False

    discovery_response = client.post("/discovery-runs/release1-demo/start")

    assert discovery_response.status_code == 200
    discovered = discovery_response.json()
    assert discovered["collector"]["status"] == "connected"
    assert discovered["discovery"] == {
        "run_id": "discovery-release1-demo-001",
        "status": "completed",
        "source": "fixture",
        "compute_nodes": 3,
        "network_segments": 3,
        "graph_nodes": 12,
        "graph_edges": 13,
        "estimate_ready": True,
    }
