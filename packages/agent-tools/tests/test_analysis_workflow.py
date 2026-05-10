from omnibridge_agent_tools.analysis_workflow import (
    run_fixture_analysis,
    run_graph_grounded_analysis,
)
from omnibridge_agent_tools.graph_knowledge import GraphKnowledgeTools
from omnibridge_canonical_graph.models import GraphTopologyEdge, ProjectTopology


class FakeTopologyRepository:
    def fetch_project_topology(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> ProjectTopology:
        return ProjectTopology(
            node_counts={"ComputeNode": 3, "Host": 1, "StorageVolume": 3},
            relationship_counts={"RUNS_ON": 3, "HAS_VOLUME": 3, "CONNECTED_TO": 3},
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


def test_fixture_analysis_returns_consultant_summary() -> None:
    result = run_fixture_analysis(
        compute_nodes=["claims-web-01", "claims-api-01", "claims-db-01"],
        blocker_count=1,
        warning_count=1,
    )

    assert result.summary.startswith("Claims Portal")
    assert result.requires_consultant_review is True
    assert result.analysis_source == "fixture"


def test_graph_grounded_analysis_uses_topology_context() -> None:
    result = run_graph_grounded_analysis(
        application_name="Claims Portal",
        project_id="project-acme-vmware-azure",
        tenant_id="tenant-acme",
        graph_tools=GraphKnowledgeTools(FakeTopologyRepository()),
        blocker_count=1,
        warning_count=1,
    )

    assert result.analysis_source == "graph"
    assert result.summary.startswith(
        "Claims Portal graph analysis: Project project-acme-vmware-azure has"
    )
    assert "Review graph evidence: claims-db-01 -[RUNS_ON]-> esx01" in result.decision_points
    assert result.graph_context_summary is not None
    assert result.graph_evidence_edges == [
        "claims-db-01 -[RUNS_ON]-> esx01",
        "claims-db-01 -[HAS_VOLUME]-> claims-db-01-disk-0",
    ]
