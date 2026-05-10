import pytest
from pydantic import ValidationError

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


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_graph_edge_rejects_confidence_outside_unit_interval(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        GraphEdge(
            id="edge-1",
            project_id="project-1",
            tenant_id="tenant-1",
            source_id="node-api",
            target_id="node-db",
            relationship_type="DEPENDS_ON",
            confidence=confidence,
        )


def test_graph_node_rejects_empty_labels() -> None:
    with pytest.raises(ValidationError):
        GraphNode(
            id="node-1",
            project_id="project-1",
            tenant_id="tenant-1",
            labels=[],
        )


def test_mutable_defaults_are_independent_between_instances() -> None:
    first_node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
    )
    second_node = GraphNode(
        id="node-2",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
    )
    first_edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-api",
        target_id="node-db",
        relationship_type="DEPENDS_ON",
    )
    second_edge = GraphEdge(
        id="edge-2",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-api",
        target_id="node-cache",
        relationship_type="DEPENDS_ON",
    )

    first_node.properties["name"] = "claims-api-01"
    first_edge.properties["port"] = 1433
    first_edge.evidence.append("observed_tcp_1433_flow")

    assert second_node.properties == {}
    assert second_edge.properties == {}
    assert second_edge.evidence == []
