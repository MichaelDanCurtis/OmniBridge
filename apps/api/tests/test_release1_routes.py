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
    assert response.json()["corridor"] == "vmware-to-azure"


def test_analysis_endpoint_returns_decision_points() -> None:
    client = TestClient(app)
    response = client.get("/analysis/release1-demo")
    assert response.status_code == 200
    assert response.json()["requires_consultant_review"] is True
