from omnibridge_canonical_graph.models import GraphEdge, GraphNode
from omnibridge_canonical_graph.repository import (
    build_node_merge,
    build_relationship_merge,
)


def test_build_node_merge_uses_labels_and_identity() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={"name": "claims-api-01"},
    )

    query, params = build_node_merge(node)

    assert "MERGE (n:GraphNode:ComputeNode:VMwareVirtualMachine {id: $id})" in query
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

    assert "MERGE (a)-[r:DEPENDS_ON {id: $id}]->(b)" in query
    assert params["source_id"] == "node-a"
    assert params["target_id"] == "node-b"
    assert params["relationship_type"] == "DEPENDS_ON"
