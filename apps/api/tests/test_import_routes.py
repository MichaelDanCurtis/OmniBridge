from fastapi.testclient import TestClient

from omnibridge_api.main import app
from omnibridge_api.routes.imports import get_graph_repository


class RecordingGraphRepository:
    def __init__(self) -> None:
        self.schema_bootstrapped = False
        self.ingested_node_count = 0
        self.ingested_edge_count = 0

    def bootstrap_schema(self) -> None:
        self.schema_bootstrapped = True

    def ingest_graph(self, nodes: list[object], edges: list[object]) -> None:
        self.ingested_node_count = len(nodes)
        self.ingested_edge_count = len(edges)


def test_import_fixture_route_returns_counts() -> None:
    client = TestClient(app)

    response = client.post(
        "/imports/vmware-fixture",
        json={"fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json"},
    )

    assert response.status_code == 200
    assert response.json()["nodes"] == 12
    assert response.json()["edges"] == 13
    assert response.json()["persisted"] is False


def test_import_fixture_route_can_persist_to_graph_repository() -> None:
    repository = RecordingGraphRepository()
    app.dependency_overrides[get_graph_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.post(
            "/imports/vmware-fixture",
            json={
                "fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
                "persist_to_neo4j": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"nodes": 12, "edges": 13, "persisted": True}
    assert repository.schema_bootstrapped is True
    assert repository.ingested_node_count == 12
    assert repository.ingested_edge_count == 13


def test_import_knowledge_seed_route_can_persist_to_graph_repository() -> None:
    repository = RecordingGraphRepository()
    app.dependency_overrides[get_graph_repository] = lambda: repository
    client = TestClient(app)

    try:
        response = client.post(
            "/imports/knowledge-seed/vmware-to-azure",
            json={
                "project_id": "project-release1-vmware-azure",
                "tenant_id": "tenant-omnibridge-demo",
                "persist_to_neo4j": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"nodes": 10, "edges": 9, "persisted": True}
    assert repository.schema_bootstrapped is True
    assert repository.ingested_node_count == 10
    assert repository.ingested_edge_count == 9


def test_import_knowledge_seed_route_requires_graph_repository_when_persisting() -> None:
    app.dependency_overrides[get_graph_repository] = lambda: None
    client = TestClient(app)

    try:
        response = client.post(
            "/imports/knowledge-seed/vmware-to-azure",
            json={
                "project_id": "project-release1-vmware-azure",
                "tenant_id": "tenant-omnibridge-demo",
                "persist_to_neo4j": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_import_fixture_route_requires_graph_repository_when_persisting() -> None:
    app.dependency_overrides[get_graph_repository] = lambda: None
    client = TestClient(app)

    try:
        response = client.post(
            "/imports/vmware-fixture",
            json={
                "fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
                "persist_to_neo4j": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_import_fixture_route_rejects_out_of_scope_path() -> None:
    client = TestClient(app)

    response = client.post(
        "/imports/vmware-fixture",
        json={"fixture_path": "pyproject.toml"},
    )

    assert response.status_code == 400


def test_import_fixture_route_rejects_missing_fixture() -> None:
    client = TestClient(app)

    response = client.post(
        "/imports/vmware-fixture",
        json={"fixture_path": "missing-fixture.json"},
    )

    assert response.status_code == 400


def test_graph_summary_route_returns_shape() -> None:
    client = TestClient(app)

    response = client.get("/graph/summary")

    assert response.status_code == 200
    summary = response.json()
    assert "compute_nodes" in summary
    assert "network_segments" in summary
