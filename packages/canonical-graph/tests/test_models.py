from omnibridge_canonical_graph.models import GraphEdge, GraphNode


def test_graph_node_requires_identity_fields() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
        properties={"name": "claims-api-01"},
    )

    assert node.id == "node-1"
    assert node.labels == ["ComputeNode"]
    assert node.properties["name"] == "claims-api-01"


def test_graph_edge_carries_confidence_and_evidence() -> None:
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-api",
        target_id="node-db",
        relationship_type="DEPENDS_ON",
        confidence=0.91,
        evidence=["observed_tcp_1433_flow"],
    )

    assert edge.relationship_type == "DEPENDS_ON"
    assert edge.confidence == 0.91
    assert edge.evidence == ["observed_tcp_1433_flow"]
