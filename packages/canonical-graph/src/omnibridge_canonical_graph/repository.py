from collections.abc import Sequence

from neo4j import Driver

from omnibridge_canonical_graph.models import GraphEdge, GraphNode


def _labels_fragment(labels: Sequence[str]) -> str:
    clean_labels = ["GraphNode", *labels]
    return ":" + ":".join(dict.fromkeys(clean_labels))


def build_node_merge(node: GraphNode) -> tuple[str, dict[str, object]]:
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
