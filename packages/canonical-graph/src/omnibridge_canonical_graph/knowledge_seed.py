from pydantic import BaseModel, ConfigDict

from omnibridge_canonical_graph.models import GraphEdge, GraphNode


class GraphKnowledgeSeed(BaseModel):
    model_config = ConfigDict(frozen=True)

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


def _node(
    *,
    id: str,
    project_id: str,
    tenant_id: str,
    labels: tuple[str, ...],
    properties: dict[str, str | int | float | bool | None | tuple[str, ...]],
) -> GraphNode:
    return GraphNode(
        id=id,
        project_id=project_id,
        tenant_id=tenant_id,
        labels=labels,
        properties=properties,
    )


def _edge(
    *,
    id: str,
    project_id: str,
    tenant_id: str,
    source_id: str,
    relationship_type: str,
    target_id: str,
    evidence: tuple[str, ...],
) -> GraphEdge:
    return GraphEdge(
        id=id,
        project_id=project_id,
        tenant_id=tenant_id,
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        evidence=evidence,
    )


def build_vmware_to_azure_knowledge_seed(
    *,
    project_id: str,
    tenant_id: str,
) -> GraphKnowledgeSeed:
    nodes = (
        _node(
            id="corridor:vmware-to-azure",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "MigrationCorridor"),
            properties={
                "name": "VMware to Azure",
                "source_platform": "vmware-vcenter",
                "target_platform": "azure",
            },
        ),
        _node(
            id="platform:vmware-vcenter",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "SourcePlatform"),
            properties={
                "name": "VMware vCenter",
                "canonical_anchor": "virtual_machine",
            },
        ),
        _node(
            id="platform:azure",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "TargetCloud"),
            properties={
                "name": "Azure",
                "canonical_anchor": "virtual_machine",
            },
        ),
        _node(
            id="service:azure-migrate",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "MigrationService"),
            properties={
                "name": "Azure Migrate",
                "execution_boundary": "deterministic_engine",
            },
        ),
        _node(
            id="pattern:azure-migrate-agentless",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "MigrationPattern"),
            properties={
                "name": "Azure Migrate agentless VMware replication",
                "execution_boundary": "deterministic_engine",
                "approval_required": True,
            },
        ),
        _node(
            id="rule:vmware.snapshot.exists",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "ReadinessRule"),
            properties={
                "name": "Existing VMware snapshots",
                "severity": "blocker",
                "detector": "deterministic_rule",
            },
        ),
        _node(
            id="rule:azure.network.mapping.missing",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "ReadinessRule"),
            properties={
                "name": "Missing Azure subnet mapping",
                "severity": "blocker",
                "detector": "deterministic_rule",
            },
        ),
        _node(
            id="playbook:remove-vmware-snapshots",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "RemediationPlaybook"),
            properties={
                "name": "Consolidate or remove VMware snapshots",
                "human_approval_required": True,
            },
        ),
        _node(
            id="playbook:map-source-portgroups",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "RemediationPlaybook"),
            properties={
                "name": "Map source port groups to Azure subnets",
                "human_approval_required": True,
            },
        ),
        _node(
            id="design-pattern:three-tier-azure-network",
            project_id=project_id,
            tenant_id=tenant_id,
            labels=("KnowledgeNode", "TargetDesignPattern"),
            properties={
                "name": "Three-tier Azure VNet with web app db subnets",
                "target_controls": ("subnets", "nsg_rules", "route_tables"),
            },
        ),
    )
    edges = (
        _edge(
            id="knowledge-edge:vmware-source-for-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="platform:vmware-vcenter",
            relationship_type="SOURCE_FOR",
            target_id="corridor:vmware-to-azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:azure-target-for-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="corridor:vmware-to-azure",
            relationship_type="TARGETS_PLATFORM",
            target_id="platform:azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:agentless-applies-to-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="pattern:azure-migrate-agentless",
            relationship_type="APPLIES_TO_CORRIDOR",
            target_id="corridor:vmware-to-azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:agentless-supported-by-azure-migrate",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="pattern:azure-migrate-agentless",
            relationship_type="SUPPORTED_BY_SERVICE",
            target_id="service:azure-migrate",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:snapshot-rule-applies-to-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="rule:vmware.snapshot.exists",
            relationship_type="APPLIES_TO_CORRIDOR",
            target_id="corridor:vmware-to-azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:snapshot-rule-remediated-by-playbook",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="rule:vmware.snapshot.exists",
            relationship_type="REMEDIATED_BY",
            target_id="playbook:remove-vmware-snapshots",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:network-rule-applies-to-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="rule:azure.network.mapping.missing",
            relationship_type="APPLIES_TO_CORRIDOR",
            target_id="corridor:vmware-to-azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:network-rule-remediated-by-playbook",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="rule:azure.network.mapping.missing",
            relationship_type="REMEDIATED_BY",
            target_id="playbook:map-source-portgroups",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
        _edge(
            id="knowledge-edge:three-tier-network-applies-to-corridor",
            project_id=project_id,
            tenant_id=tenant_id,
            source_id="design-pattern:three-tier-azure-network",
            relationship_type="APPLIES_TO_CORRIDOR",
            target_id="corridor:vmware-to-azure",
            evidence=("omnibridge.release1.knowledge_seed",),
        ),
    )

    return GraphKnowledgeSeed(nodes=nodes, edges=edges)
