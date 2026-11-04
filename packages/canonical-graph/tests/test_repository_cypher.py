import pytest

from omnibridge_canonical_graph.models import GraphEdge, GraphNode
import omnibridge_canonical_graph.repository as repository
from omnibridge_canonical_graph.repository import (
    build_node_merge,
    build_relationship_merge,
)


class RecordingSession:
    def __init__(self, results: list[list[dict[str, object]]] | None = None) -> None:
        self.queries: list[tuple[str, dict[str, object]]] = []
        self._results = list(results or [])

    def __enter__(self) -> "RecordingSession":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def run(self, query: str, **params: object) -> list[dict[str, object]]:
        self.queries.append((query, params))
        if self._results:
            return self._results.pop(0)
        return []


class RecordingDriver:
    def __init__(self, results: list[list[dict[str, object]]] | None = None) -> None:
        self.session_instance = RecordingSession(results)

    def session(self) -> RecordingSession:
        return self.session_instance


def test_build_node_merge_uses_labels_and_identity() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={"name": "claims-api-01"},
    )

    query, params = build_node_merge(node)

    assert (
        "MERGE (n:GraphNode:ComputeNode:VMwareVirtualMachine "
        "{id: $id, project_id: $project_id, tenant_id: $tenant_id})"
    ) in query
    assert params["id"] == "node-1"
    assert params["properties"]["name"] == "claims-api-01"


def test_build_relationship_merge_uses_relationship_type() -> None:
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-a",
        target_id="node-b",
        relationship_type="DEPENDS_ON",
        confidence=0.9,
    )

    query, params = build_relationship_merge(edge)

    assert (
        "MATCH (a:GraphNode {id: $source_id, "
        "project_id: $project_id, tenant_id: $tenant_id})"
    ) in query
    assert (
        "MATCH (b:GraphNode {id: $target_id, "
        "project_id: $project_id, tenant_id: $tenant_id})"
    ) in query
    assert (
        "MERGE (a)-[r:DEPENDS_ON "
        "{id: $id, project_id: $project_id, tenant_id: $tenant_id}]->(b)"
    ) in query
    assert params["source_id"] == "node-a"
    assert params["target_id"] == "node-b"
    assert params["relationship_type"] == "DEPENDS_ON"


def test_build_node_merge_rejects_reserved_properties() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
        properties={"id": "corrupt-node-id"},
    )

    with pytest.raises(ValueError, match="reserved graph properties"):
        build_node_merge(node)


def test_build_relationship_merge_rejects_reserved_properties() -> None:
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-a",
        target_id="node-b",
        relationship_type="DEPENDS_ON",
        properties={"confidence": 0.1},
    )

    with pytest.raises(ValueError, match="reserved graph properties"):
        build_relationship_merge(edge)


def test_build_schema_statements_define_project_scoped_graph_indexes() -> None:
    statements = repository.build_schema_statements()

    assert any(
        "CREATE CONSTRAINT omnibridge_graph_node_identity" in statement
        and "FOR (n:GraphNode)" in statement
        for statement in statements
    )
    assert any("CREATE INDEX omnibridge_graph_node_project" in statement for statement in statements)
    assert any(
        "CREATE INDEX omnibridge_relationship_project" in statement
        for statement in statements
    )


def test_repository_bootstrap_schema_runs_all_schema_statements() -> None:
    driver = RecordingDriver()

    repository.Neo4jGraphRepository(driver).bootstrap_schema()

    assert [query for query, _params in driver.session_instance.queries] == list(
        repository.build_schema_statements()
    )


def test_repository_ingest_graph_writes_nodes_before_edges() -> None:
    node_a = GraphNode(
        id="node-a",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
        properties={"name": "claims-api-01"},
    )
    node_b = GraphNode(
        id="node-b",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["NetworkSegment"],
        properties={"name": "dvpg-app-prod"},
    )
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-a",
        target_id="node-b",
        relationship_type="CONNECTED_TO",
    )
    driver = RecordingDriver()

    repository.Neo4jGraphRepository(driver).ingest_graph(
        nodes=[node_a, node_b],
        edges=[edge],
    )

    queries = [query for query, _params in driver.session_instance.queries]
    assert queries[0].startswith("MERGE (n:GraphNode:ComputeNode")
    assert queries[1].startswith("MERGE (n:GraphNode:NetworkSegment")
    assert "MERGE (a)-[r:CONNECTED_TO" in queries[2]


def test_fetch_project_topology_returns_counts_and_limited_edges() -> None:
    driver = RecordingDriver(
        results=[
            [
                {"label": "ComputeNode", "count": 3},
                {"label": "Host", "count": 1},
            ],
            [{"relationship_type": "RUNS_ON", "count": 3}],
            [
                {
                    "source_id": "vm:vm-103",
                    "source_name": "claims-db-01",
                    "relationship_type": "RUNS_ON",
                    "target_id": "host:host-101",
                    "target_name": "esx01",
                    "confidence": 1.0,
                    "evidence": ["vmware.vm.host_moid"],
                }
            ],
        ]
    )

    topology = repository.Neo4jGraphRepository(driver).fetch_project_topology(
        project_id="project-1",
        tenant_id="tenant-1",
        edge_limit=25,
    )

    assert topology.node_counts == {"ComputeNode": 3, "Host": 1}
    assert topology.relationship_counts == {"RUNS_ON": 3}
    assert topology.edges[0].source_name == "claims-db-01"
    assert topology.edges[0].relationship_type == "RUNS_ON"
    assert topology.edges[0].target_name == "esx01"
    assert topology.edges[0].evidence == ("vmware.vm.host_moid",)
    assert all(
        params["project_id"] == "project-1" and params["tenant_id"] == "tenant-1"
        for _query, params in driver.session_instance.queries
    )
    assert driver.session_instance.queries[-1][1]["edge_limit"] == 25
