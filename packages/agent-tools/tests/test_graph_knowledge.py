from omnibridge_agent_tools.graph_knowledge import GraphKnowledgeTools
from omnibridge_canonical_graph.models import (
    GraphTopologyEdge,
    ProjectTopology,
)


class FakeGraphRepository:
    def __init__(self, topology: ProjectTopology) -> None:
        self.topology = topology
        self.calls: list[tuple[str, str, int]] = []

    def fetch_project_topology(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> ProjectTopology:
        self.calls.append((project_id, tenant_id, edge_limit))
        return self.topology


def test_graph_knowledge_tool_returns_bounded_project_context() -> None:
    topology = ProjectTopology(
        node_counts={"ComputeNode": 3, "Host": 1, "StorageVolume": 3},
        relationship_counts={"RUNS_ON": 3, "HAS_VOLUME": 3},
        edges=(
            GraphTopologyEdge(
                source_id="vm:vm-103",
                source_name="claims-db-01",
                relationship_type="RUNS_ON",
                target_id="host:host-101",
                target_name="esx01",
                evidence=("vmware.vm.host_moid",),
            ),
            GraphTopologyEdge(
                source_id="vm:vm-103",
                source_name="claims-db-01",
                relationship_type="HAS_VOLUME",
                target_id="volume:vm-103:0",
                target_name="claims-db-01-disk-0",
                evidence=("vmware.vm.disks",),
            ),
        ),
    )
    repository = FakeGraphRepository(topology)

    result = GraphKnowledgeTools(repository).get_project_topology_context(
        project_id="project-release1-vmware-azure",
        tenant_id="tenant-omnibridge-demo",
        edge_limit=25,
    )

    assert repository.calls == [("project-release1-vmware-azure", "tenant-omnibridge-demo", 25)]
    assert result.summary == (
        "Project project-release1-vmware-azure has 7 graph nodes across 3 labels "
        "and 6 relationships across 2 types."
    )
    assert result.node_counts["ComputeNode"] == 3
    assert result.relationship_counts["RUNS_ON"] == 3
    assert result.evidence_edges == [
        "claims-db-01 -[RUNS_ON]-> esx01",
        "claims-db-01 -[HAS_VOLUME]-> claims-db-01-disk-0",
    ]
