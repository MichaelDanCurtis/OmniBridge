from collections.abc import Mapping, Sequence

from neo4j import Driver

from omnibridge_canonical_graph.models import (
    GraphEdge,
    GraphNode,
    GraphTopologyEdge,
    ProjectTopology,
)

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

_SCHEMA_STATEMENTS = (
    (
        "CREATE CONSTRAINT omnibridge_graph_node_identity IF NOT EXISTS "
        "FOR (n:GraphNode) "
        "REQUIRE (n.id, n.project_id, n.tenant_id) IS UNIQUE"
    ),
    (
        "CREATE INDEX omnibridge_graph_node_project IF NOT EXISTS "
        "FOR (n:GraphNode) "
        "ON (n.project_id, n.tenant_id)"
    ),
    (
        "CREATE INDEX omnibridge_graph_node_name IF NOT EXISTS "
        "FOR (n:GraphNode) "
        "ON (n.name)"
    ),
    (
        "CREATE INDEX omnibridge_relationship_project IF NOT EXISTS "
        "FOR ()-[r]-() "
        "ON (r.project_id, r.tenant_id)"
    ),
)


def build_schema_statements() -> tuple[str, ...]:
    return _SCHEMA_STATEMENTS


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
        f"MERGE (n{labels} "
        "{id: $id, project_id: $project_id, tenant_id: $tenant_id}) "
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
        "MATCH (a:GraphNode "
        "{id: $source_id, project_id: $project_id, tenant_id: $tenant_id}) "
        "MATCH (b:GraphNode "
        "{id: $target_id, project_id: $project_id, tenant_id: $tenant_id}) "
        f"MERGE (a)-[r:{edge.relationship_type} "
        "{id: $id, project_id: $project_id, tenant_id: $tenant_id}]->(b) "
        "SET r.project_id = $project_id, "
        "r.tenant_id = $tenant_id, "
        "r.confidence = $confidence, "
        "r.evidence = $evidence, "
        "r += $properties "
        "RETURN r.id AS id"
    )
    params = edge.model_dump(mode="json")
    return query, params


def build_node_counts_query(project_id: str, tenant_id: str) -> tuple[str, dict[str, object]]:
    query = (
        "MATCH (n:GraphNode {project_id: $project_id, tenant_id: $tenant_id}) "
        "UNWIND labels(n) AS label "
        "RETURN label AS label, count(*) AS count "
        "ORDER BY label"
    )
    return query, {"project_id": project_id, "tenant_id": tenant_id}


def build_relationship_counts_query(
    project_id: str,
    tenant_id: str,
) -> tuple[str, dict[str, object]]:
    query = (
        "MATCH (:GraphNode {project_id: $project_id, tenant_id: $tenant_id})"
        "-[r]->"
        "(:GraphNode {project_id: $project_id, tenant_id: $tenant_id}) "
        "WHERE r.project_id = $project_id AND r.tenant_id = $tenant_id "
        "RETURN type(r) AS relationship_type, count(*) AS count "
        "ORDER BY relationship_type"
    )
    return query, {"project_id": project_id, "tenant_id": tenant_id}


def build_topology_edges_query(
    project_id: str,
    tenant_id: str,
    edge_limit: int,
) -> tuple[str, dict[str, object]]:
    query = (
        "MATCH (source:GraphNode {project_id: $project_id, tenant_id: $tenant_id})"
        "-[r]->"
        "(target:GraphNode {project_id: $project_id, tenant_id: $tenant_id}) "
        "WHERE r.project_id = $project_id AND r.tenant_id = $tenant_id "
        "RETURN source.id AS source_id, "
        "coalesce(source.name, source.id) AS source_name, "
        "type(r) AS relationship_type, "
        "target.id AS target_id, "
        "coalesce(target.name, target.id) AS target_name, "
        "coalesce(r.confidence, 1.0) AS confidence, "
        "coalesce(r.evidence, []) AS evidence "
        "ORDER BY source_name, relationship_type, target_name "
        "LIMIT $edge_limit"
    )
    return query, {
        "project_id": project_id,
        "tenant_id": tenant_id,
        "edge_limit": edge_limit,
    }


def _records_to_counts(
    records: Sequence[Mapping[str, object]],
    key_name: str,
) -> dict[str, int]:
    return {
        str(record[key_name]): int(record["count"])
        for record in records
    }


def _records_to_topology_edges(
    records: Sequence[Mapping[str, object]],
) -> tuple[GraphTopologyEdge, ...]:
    return tuple(
        GraphTopologyEdge(
            source_id=str(record["source_id"]),
            source_name=str(record["source_name"]),
            relationship_type=str(record["relationship_type"]),
            target_id=str(record["target_id"]),
            target_name=str(record["target_name"]),
            confidence=float(record.get("confidence", 1.0)),
            evidence=tuple(str(item) for item in record.get("evidence", []) or []),
        )
        for record in records
    )


class Neo4jGraphRepository:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def bootstrap_schema(self) -> None:
        with self._driver.session() as session:
            for statement in build_schema_statements():
                session.run(statement)

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

    def ingest_graph(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        self.upsert_nodes(nodes)
        self.upsert_edges(edges)

    def fetch_project_topology(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> ProjectTopology:
        with self._driver.session() as session:
            node_query, node_params = build_node_counts_query(project_id, tenant_id)
            relationship_query, relationship_params = build_relationship_counts_query(
                project_id,
                tenant_id,
            )
            edge_query, edge_params = build_topology_edges_query(
                project_id,
                tenant_id,
                edge_limit,
            )

            node_counts = _records_to_counts(
                list(session.run(node_query, **node_params)),
                key_name="label",
            )
            relationship_counts = _records_to_counts(
                list(session.run(relationship_query, **relationship_params)),
                key_name="relationship_type",
            )
            edges = _records_to_topology_edges(list(session.run(edge_query, **edge_params)))

        return ProjectTopology(
            node_counts=node_counts,
            relationship_counts=relationship_counts,
            edges=edges,
        )
