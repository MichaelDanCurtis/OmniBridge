from collections.abc import Mapping, Sequence

from neo4j import Driver

from omnibridge_canonical_graph.models import GraphEdge, GraphNode

_RESERVED_NODE_PROPERTIES = frozenset({"id", "project_id", "tenant_id", "labels"})
_RESERVED_EDGE_PROPERTIES = frozenset(
    {
        "id",
        "project_id",
        "tenant_id",
        "source_id",
        "target_id",
        "relationship_type",
        "confidence",
        "evidence",
    }
)


def _labels_fragment(labels: Sequence[str]) -> str:
    clean_labels = ["GraphNode", *labels]
    return ":" + ":".join(dict.fromkeys(clean_labels))


def _reject_reserved_properties(
    properties: Mapping[str, object],
    reserved: frozenset[str],
) -> None:
    conflicts = sorted(set(properties).intersection(reserved))
    if conflicts:
        conflict_list = ", ".join(conflicts)
        raise ValueError(f"properties cannot use reserved graph properties: {conflict_list}")


def build_node_merge(node: GraphNode) -> tuple[str, dict[str, object]]:
    _reject_reserved_properties(node.properties, _RESERVED_NODE_PROPERTIES)
    labels = _labels_fragment(node.labels)
    query = (
        f"MERGE (n{labels} {{id: $id}}) "
        "SET n.project_id = $project_id, "
        "n.tenant_id = $tenant_id, "
        "n += $properties "
        "RETURN n.id AS id"
    )
    params = node.model_dump(mode="json")
    return query, params


def build_relationship_merge(edge: GraphEdge) -> tuple[str, dict[str, object]]:
    _reject_reserved_properties(edge.properties, _RESERVED_EDGE_PROPERTIES)
    query = (
        "MATCH (a:GraphNode {id: $source_id}) "
        "MATCH (b:GraphNode {id: $target_id}) "
        f"MERGE (a)-[r:{edge.relationship_type} {{id: $id}}]->(b) "
        "SET r.project_id = $project_id, "
        "r.tenant_id = $tenant_id, "
        "r.confidence = $confidence, "
        "r.evidence = $evidence, "
        "r += $properties "
        "RETURN r.id AS id"
    )
    params = edge.model_dump(mode="json")
    return query, params


class Neo4jGraphRepository:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def upsert_nodes(self, nodes: list[GraphNode]) -> None:
        with self._driver.session() as session:
            for node in nodes:
                query, params = build_node_merge(node)
                session.run(query, **params)

    def upsert_edges(self, edges: list[GraphEdge]) -> None:
        with self._driver.session() as session:
            for edge in edges:
                query, params = build_relationship_merge(edge)
                session.run(query, **params)
