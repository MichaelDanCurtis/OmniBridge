from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_estimate_endpoint_returns_commercial_estimate() -> None:
    client = TestClient(app)
    response = client.get("/estimates/release1-demo")
    assert response.status_code == 200
    assert response.json()["project_package"] == "assessment"


def test_blueprint_endpoint_returns_vmware_to_azure_blueprint() -> None:
    client = TestClient(app)
    response = client.get("/blueprints/release1-demo")
    assert response.status_code == 200
    blueprint = response.json()
    assert blueprint["corridor"] == "vmware-to-azure"
    assert blueprint["compute_node_names"] == [
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    ]
    assert blueprint["waves"][0]["compute_nodes"] == [
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    ]
    assert "source_shutdown_approval" in blueprint["approval_gates"]


def test_analysis_endpoint_returns_decision_points() -> None:
    client = TestClient(app)
    response = client.get("/analysis/release1-demo")
    assert response.status_code == 200
    assert response.json()["requires_consultant_review"] is True


def test_artifact_endpoint_returns_markdown_assessment() -> None:
    client = TestClient(app)
    response = client.get("/artifacts/release1-assessment.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# ACME VMware-to-Azure Assessment" in response.text
