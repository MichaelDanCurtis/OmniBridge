from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_import_fixture_route_returns_counts() -> None:
    client = TestClient(app)

    response = client.post(
        "/imports/vmware-fixture",
        json={"fixture_path": "corridors/vmware-to-azure/fixtures/acme-small-estate.json"},
    )

    assert response.status_code == 200
    assert response.json()["nodes"] == 6
    assert response.json()["edges"] == 3


def test_graph_summary_route_returns_shape() -> None:
    client = TestClient(app)

    response = client.get("/graph/summary")

    assert response.status_code == 200
    summary = response.json()
    assert "compute_nodes" in summary
    assert "network_segments" in summary
