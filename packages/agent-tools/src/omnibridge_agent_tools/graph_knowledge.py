from typing import Protocol

from omnibridge_agent_tools.models import GraphTopologyContext
from omnibridge_canonical_graph.models import ProjectTopology


class ProjectTopologyRepository(Protocol):
    def fetch_project_topology(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> ProjectTopology:
        pass


def _edge_evidence(edge: object) -> str:
    source_name = getattr(edge, "source_name")
    relationship_type = getattr(edge, "relationship_type")
    target_name = getattr(edge, "target_name")
    return f"{source_name} -[{relationship_type}]-> {target_name}"


def _summarize_topology(project_id: str, topology: ProjectTopology) -> str:
    node_total = sum(topology.node_counts.values())
    relationship_total = sum(topology.relationship_counts.values())
    return (
        f"Project {project_id} has {node_total} graph nodes across "
        f"{len(topology.node_counts)} labels and {relationship_total} relationships "
        f"across {len(topology.relationship_counts)} types."
    )


class GraphKnowledgeTools:
    def __init__(self, repository: ProjectTopologyRepository) -> None:
        self._repository = repository

    def get_project_topology_context(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> GraphTopologyContext:
        topology = self._repository.fetch_project_topology(
            project_id=project_id,
            tenant_id=tenant_id,
            edge_limit=edge_limit,
        )

        return GraphTopologyContext(
            summary=_summarize_topology(project_id, topology),
            node_counts=topology.node_counts,
            relationship_counts=topology.relationship_counts,
            evidence_edges=[_edge_evidence(edge) for edge in topology.edges],
        )
