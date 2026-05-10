import pytest

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
