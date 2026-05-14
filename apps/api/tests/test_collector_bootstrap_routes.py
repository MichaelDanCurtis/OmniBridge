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


def test_collector_bootstrap_creates_pending_registration_package() -> None:
    client = TestClient(app)

    response = client.post("/collectors/release1-demo/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["collector"]["collector_id"] == "collector-release1-demo"
    assert payload["collector"]["status"] == "pending_registration"
    assert payload["collector"]["last_heartbeat_at"] is None
    assert payload["registration"]["collector_id"] == "collector-release1-demo"
    assert len(payload["registration"]["registration_token"]) >= 24
    assert payload["registration"]["api_url"] == "http://127.0.0.1:8001"
    assert "omnibridge-collector run" in payload["registration"]["install_command"]
    assert "--api-url http://127.0.0.1:8001" in payload["registration"]["install_command"]


def test_collector_registers_with_bootstrap_token_and_then_heartbeats() -> None:
    client = TestClient(app)
    bootstrap = client.post("/collectors/release1-demo/bootstrap").json()
    registration_token = bootstrap["registration"]["registration_token"]

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
    assert registered["collector"]["version"] == "0.1.0"
    assert registered["collector"]["capabilities"] == ["fixture_discovery", "heartbeat"]
    assert registered["collector"]["last_heartbeat_at"] is not None

    heartbeat_response = client.post(
        "/collectors/collector-release1-demo/heartbeat",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert heartbeat_response.status_code == 200
    assert heartbeat_response.json()["collector"]["status"] == "online"


def test_collector_registration_rejects_invalid_token() -> None:
    client = TestClient(app)
    client.post("/collectors/release1-demo/bootstrap")

    response = client.post(
        "/collectors/release1-demo/register",
        json={
            "collector_id": "collector-release1-demo",
            "registration_token": "wrong-token",
            "version": "0.1.0",
            "capabilities": ["heartbeat"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid collector registration token."


def test_collector_registration_returns_not_found_for_unknown_collector() -> None:
    client = TestClient(app)

    response = client.post(
        "/collectors/release1-demo/register",
        json={
            "collector_id": "missing-collector",
            "registration_token": "token-abc",
            "version": "0.1.0",
            "capabilities": ["heartbeat"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Collector was not bootstrapped."


def test_collector_heartbeat_returns_not_found_for_unknown_collector() -> None:
    client = TestClient(app)

    response = client.post(
        "/collectors/missing-collector/heartbeat",
        json={
            "registration_token": "token-abc",
            "version": "0.1.0",
            "capabilities": ["heartbeat"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Collector was not bootstrapped."


def test_bootstrap_does_not_rotate_an_online_collector_token() -> None:
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

    response = client.post("/collectors/release1-demo/bootstrap")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Collector is already online. Revoke or rotate it explicitly before bootstrapping."
    )


def test_discovery_requires_online_registered_collector() -> None:
    client = TestClient(app)
    client.post("/collectors/release1-demo/bootstrap")

    response = client.post("/discovery-runs/release1-demo/start")

    assert response.status_code == 409
    assert response.json()["detail"] == "Collector must be online before discovery can run."


def test_registered_collector_claim_with_no_work_returns_null_job() -> None:
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

    response = client.post(
        "/collectors/collector-release1-demo/jobs/claim",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["collector"]["status"] == "online"
    assert payload["job"] is None


def test_queued_discovery_job_is_labeled_as_collector_sourced_work() -> None:
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

    queued_response = client.post("/discovery-runs/release1-demo/start")
    claim_response = client.post(
        "/collectors/collector-release1-demo/jobs/claim",
        json={
            "registration_token": registration_token,
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert queued_response.status_code == 200
    assert queued_response.json()["discovery"]["source"] == "collector"
    assert claim_response.status_code == 200
    assert claim_response.json()["job"]["parameters"] == {
        "source": "collector",
        "fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
    }


def test_collector_job_claim_rejects_invalid_token() -> None:
    client = TestClient(app)
    client.post("/collectors/release1-demo/bootstrap")

    response = client.post(
        "/collectors/collector-release1-demo/jobs/claim",
        json={
            "registration_token": "wrong-token",
            "version": "0.1.0",
            "capabilities": ["fixture_discovery", "heartbeat"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid collector registration token."


def test_collector_job_completion_requires_claimed_running_job() -> None:
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

    response = client.post(
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

    assert response.status_code == 409
    assert response.json()["detail"] == "Collector job is not running for this collector."
