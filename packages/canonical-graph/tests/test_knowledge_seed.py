from omnibridge_canonical_graph.knowledge_seed import (
    build_vmware_to_azure_knowledge_seed,
)


def test_vmware_to_azure_knowledge_seed_contains_corridor_patterns_and_rules() -> None:
    seed = build_vmware_to_azure_knowledge_seed(
        project_id="knowledge-project",
        tenant_id="tenant-1",
    )

    nodes_by_id = {node.id: node for node in seed.nodes}
    edge_triples = {
        (edge.source_id, edge.relationship_type, edge.target_id)
        for edge in seed.edges
    }

    assert nodes_by_id["corridor:vmware-to-azure"].properties["name"] == "VMware to Azure"
    assert nodes_by_id["pattern:azure-migrate-agentless"].properties[
        "execution_boundary"
    ] == "deterministic_engine"
    assert nodes_by_id["rule:vmware.snapshot.exists"].properties["severity"] == "blocker"
    assert nodes_by_id["playbook:remove-vmware-snapshots"].properties[
        "human_approval_required"
    ] is True
    assert (
        "pattern:azure-migrate-agentless",
        "SUPPORTED_BY_SERVICE",
        "service:azure-migrate",
    ) in edge_triples
    assert (
        "rule:vmware.snapshot.exists",
        "REMEDIATED_BY",
        "playbook:remove-vmware-snapshots",
    ) in edge_triples
    assert (
        "design-pattern:three-tier-azure-network",
        "APPLIES_TO_CORRIDOR",
        "corridor:vmware-to-azure",
    ) in edge_triples


def test_vmware_to_azure_knowledge_seed_is_project_scoped() -> None:
    seed = build_vmware_to_azure_knowledge_seed(
        project_id="knowledge-project",
        tenant_id="tenant-1",
    )

    assert {node.project_id for node in seed.nodes} == {"knowledge-project"}
    assert {edge.project_id for edge in seed.edges} == {"knowledge-project"}
    assert {node.tenant_id for node in seed.nodes} == {"tenant-1"}
    assert {edge.tenant_id for edge in seed.edges} == {"tenant-1"}
