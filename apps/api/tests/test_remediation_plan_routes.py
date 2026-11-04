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


def test_remediation_plan_requires_discovery() -> None:
    client = TestClient(app)

    response = client.post(
        "/remediation-plans/release1-demo",
        json={"compute_nodes": ["claims-db-01"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Discovery must complete before remediation planning can run."
    )


def test_remediation_plan_returns_rule_backed_tasks_for_selected_vms() -> None:
    client = TestClient(app)
    _complete_discovery(client)

    response = client.post(
        "/remediation-plans/release1-demo",
        json={"compute_nodes": ["claims-db-01"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["plan_id"] == "remediation-wave-001"
    assert payload["status"] == "consultant_review_required"
    assert payload["task_count"] == 2
    assert payload["next_action"] == "Assign remediation tasks before test migration."
    assert payload["tasks"][0] == {
        "task_id": "remediate-claims-db-01-vmware-snapshot-exists",
        "target_name": "claims-db-01",
        "rule_id": "vmware.snapshot.exists",
        "severity": "blocker",
        "owner_role": "VMware administrator",
        "automation_mode": "human_approved_manual_step",
        "approval_required": True,
        "recommended_action": "Consolidate or remove VMware snapshots before replication.",
    }
    assert payload["tasks"][1]["rule_id"] == "vmware.tools.outdated"
    assert payload["tasks"][1]["severity"] == "warning"


def test_remediation_plan_returns_no_action_for_clean_scope() -> None:
    client = TestClient(app)
    _complete_discovery(client)

    response = client.post(
        "/remediation-plans/release1-demo",
        json={"compute_nodes": ["claims-web-01"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "plan_id": "remediation-wave-001",
        "status": "no_action_required",
        "task_count": 0,
        "tasks": [],
        "next_action": "Continue to test migration approval.",
    }
