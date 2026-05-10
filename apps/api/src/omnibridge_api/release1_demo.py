from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omnibridge_agent_tools.models import AnalysisResult
from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis
from omnibridge_api.settings import settings
from omnibridge_azure_migrate_adapter import (
    AzureMigrateMachineRef,
    AzureMigrateOperationPlan,
    AzureMigrateOperationPlanner,
    AzureMigrateProjectRef,
)
from omnibridge_blueprint_engine.artifacts import (
    render_assessment_markdown,
    render_blueprint_yaml,
    render_runbook_markdown,
    render_terraform_main_tf,
)
from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint
from omnibridge_blueprint_engine.models import MigrationBlueprint
from omnibridge_canonical_graph.models import GraphNode
from omnibridge_estimator.models import CommercialEstimate
from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure
from omnibridge_rules_engine.models import ReadinessFinding
from omnibridge_rules_engine.vmware_readiness import evaluate_vmware_vm
from omnibridge_validation_engine.models import ValidationEvidence
from omnibridge_validation_engine.vmware_to_azure import build_release1_validation_evidence
from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import MappedGraph, map_fixture_to_graph
from omnibridge_workflow_engine.models import (
    ApprovalLedger,
    ProjectWorkflowSnapshot,
    WorkflowState,
)


_REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RELEASE1_FIXTURE_PATH = (
    _REPO_ROOT / "corridors" / "vmware-to-azure" / "fixtures" / "acme-small-estate.json"
)
APPLICATION_NAME = "Claims Portal"
PROJECT_NAME = "ACME VMware-to-Azure Assessment"


@dataclass(frozen=True)
class Release1Demo:
    graph: MappedGraph
    graph_summary: dict[str, int]
    readiness_findings: list[ReadinessFinding]
    estimate: CommercialEstimate
    blueprint: MigrationBlueprint
    analysis: AnalysisResult
    execution_plan: AzureMigrateOperationPlan
    validation_evidence: ValidationEvidence
    assessment_markdown: str
    blueprint_yaml: str
    runbook_markdown: str
    terraform_main_tf: str
    workspace: dict[str, Any]


def _has_label(node: GraphNode, label: str) -> bool:
    return label in node.labels


def _compute_nodes(graph: MappedGraph) -> list[GraphNode]:
    return [node for node in graph.nodes if _has_label(node, "ComputeNode")]


def _network_segments(graph: MappedGraph) -> list[GraphNode]:
    return [node for node in graph.nodes if _has_label(node, "NetworkSegment")]


def _compute_node_names(nodes: list[GraphNode]) -> list[str]:
    return [str(node.properties["name"]) for node in nodes]


def _storage_gb(fixture: dict[str, Any]) -> int:
    return sum(
        int(disk.get("size_gb", 0))
        for vm in fixture.get("vms", [])
        for disk in vm.get("disks", [])
    )


def _vm_storage_gb(vm: dict[str, Any]) -> int:
    return sum(int(disk.get("size_gb", 0)) for disk in vm.get("disks", []))


def _readiness_findings(nodes: list[GraphNode]) -> list[ReadinessFinding]:
    return [
        finding
        for node in nodes
        for finding in evaluate_vmware_vm(node)
    ]


def _node_display_name(node: GraphNode) -> str:
    name = node.properties.get("name")
    if isinstance(name, str):
        return name
    return node.id


def _build_topology(graph: MappedGraph) -> dict[str, Any]:
    nodes_by_id = {node.id: node for node in graph.nodes}
    node_counts = Counter(label for node in graph.nodes for label in node.labels)
    relationship_counts = Counter(edge.relationship_type for edge in graph.edges)
    edges = [
        {
            "source_id": edge.source_id,
            "source_name": _node_display_name(nodes_by_id[edge.source_id]),
            "relationship_type": edge.relationship_type,
            "target_id": edge.target_id,
            "target_name": _node_display_name(nodes_by_id[edge.target_id]),
            "confidence": edge.confidence,
            "evidence": list(edge.evidence),
        }
        for edge in graph.edges
    ]

    return {
        "node_counts": dict(sorted(node_counts.items())),
        "relationship_counts": dict(sorted(relationship_counts.items())),
        "edges": edges,
    }


def _target_subnet(source_portgroup: str) -> str:
    normalized = source_portgroup.lower()
    if "web" in normalized:
        return "snet-web"
    if "app" in normalized:
        return "snet-app"
    if "db" in normalized:
        return "snet-db"
    return "snet-shared"


def _security_intent(target_subnet: str) -> str:
    match target_subnet:
        case "snet-web":
            return "Allow HTTPS from application gateway or approved ingress."
        case "snet-app":
            return "Allow application traffic from web tier only."
        case "snet-db":
            return "Allow SQL traffic from app tier only."
        case _:
            return "Requires consultant review before NSG generation."


def _vm_size(vm: dict[str, Any]) -> str:
    cpu = int(vm["cpu"])
    memory_mb = int(vm["memory_mb"])
    if cpu >= 8 or memory_mb >= 32768:
        return "Standard_D8s_v5"
    if cpu >= 4 or memory_mb >= 16384:
        return "Standard_D4s_v5"
    return "Standard_D2s_v5"


def _disk_type(vm: dict[str, Any], target_subnet: str) -> str:
    if target_subnet == "snet-db" or _vm_storage_gb(vm) >= 512:
        return "Premium SSD"
    return "Standard SSD"


def _target_subnet_id(target_subnet: str) -> str:
    return (
        "/subscriptions/sub-acme-prod/resourceGroups/rg-network/providers/"
        f"Microsoft.Network/virtualNetworks/vnet-prod/subnets/{target_subnet}"
    )


def _build_execution_plan(fixture: dict[str, Any]) -> AzureMigrateOperationPlan:
    networks_by_moid = {network["moid"]: network for network in fixture["networks"]}
    machines = []

    for vm in fixture["vms"]:
        primary_nic = vm["nics"][0]
        source_network = networks_by_moid[primary_nic["network_moid"]]
        target_subnet = _target_subnet(str(source_network["name"]))
        machines.append(
            AzureMigrateMachineRef(
                vm_moid=str(vm["moid"]),
                vm_name=str(vm["name"]),
                target_vm_size=_vm_size(vm),
                target_subnet_id=_target_subnet_id(target_subnet),
            )
        )

    return AzureMigrateOperationPlanner().plan_agentless_vmware_wave(
        project=AzureMigrateProjectRef(
            subscription_id="sub-acme-prod",
            resource_group="rg-migrate-prod",
            project_name="omni-acme-release1",
            region="westus2",
        ),
        wave_id="wave-001",
        source_machines=tuple(machines),
    )


def _readiness_status(vm_id: str, findings: list[ReadinessFinding]) -> str:
    vm_findings = [finding for finding in findings if finding.target_node_id == vm_id]
    if any(finding.severity == "blocker" for finding in vm_findings):
        return "Blocked"
    if any(finding.severity == "warning" for finding in vm_findings):
        return "Needs review"
    return "Ready"


def _build_workspace(
    fixture: dict[str, Any],
    graph: MappedGraph,
    graph_summary: dict[str, int],
    findings: list[ReadinessFinding],
    estimate: CommercialEstimate,
    blueprint: MigrationBlueprint,
    analysis: AnalysisResult,
    execution_plan: AzureMigrateOperationPlan,
    validation_evidence: ValidationEvidence,
) -> dict[str, Any]:
    networks_by_moid = {network["moid"]: network for network in fixture["networks"]}
    node_names = {
        f"vm:{vm['moid']}": vm["name"]
        for vm in fixture["vms"]
    }
    blocker_count = sum(finding.severity == "blocker" for finding in findings)
    warning_count = sum(finding.severity == "warning" for finding in findings)
    network_mappings = [
        {
            "source_portgroup": network["name"],
            "vlan": network["vlan"],
            "target_vnet": "vnet-prod",
            "target_subnet": _target_subnet(str(network["name"])),
            "security_intent": _security_intent(_target_subnet(str(network["name"]))),
        }
        for network in fixture["networks"]
    ]
    vms: list[dict[str, Any]] = []

    for vm in fixture["vms"]:
        vm_id = f"vm:{vm['moid']}"
        primary_nic = vm["nics"][0]
        source_network = networks_by_moid[primary_nic["network_moid"]]
        target_subnet = _target_subnet(str(source_network["name"]))
        vms.append(
            {
                "name": vm["name"],
                "moid": vm["moid"],
                "cpu": vm["cpu"],
                "memory_mb": vm["memory_mb"],
                "guest_os": vm["guest_os"],
                "tools_status": vm["tools_status"],
                "snapshot_count": vm["snapshot_count"],
                "disk_gb": _vm_storage_gb(vm),
                "source_network": source_network["name"],
                "observed_ip": primary_nic["ip"],
                "readiness": _readiness_status(vm_id, findings),
                "target": {
                    "region": "westus2",
                    "resource_group": "rg-claims-prod",
                    "subnet": target_subnet,
                    "vm_size": _vm_size(vm),
                    "disk_type": _disk_type(vm, target_subnet),
                },
            }
        )

    return {
        "project": {
            "name": PROJECT_NAME,
            "tenant_id": fixture["tenant_id"],
            "corridor": "vmware-to-azure",
            "source": {
                "platform": "vmware-vcenter",
                "vcenter": fixture["vcenter"],
                "datacenter": fixture["datacenter"],
            },
            "target": {
                "cloud": "azure",
                "region": "westus2",
                "resource_group": "rg-claims-prod",
            },
        },
        "summary": {
            **graph_summary,
            "blockers": blocker_count,
            "warnings": warning_count,
            "total_storage_gb": _storage_gb(fixture),
        },
        "application": {
            "name": APPLICATION_NAME,
            "members": list(blueprint.compute_node_names),
        },
        "inventory": {
            "clusters": fixture["clusters"],
            "datastores": fixture["datastores"],
            "networks": fixture["networks"],
            "vms": vms,
        },
        "graph_ingest": {
            "source": "fixture",
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "persisted": False,
            "neo4j_configured": bool(settings.neo4j_uri and settings.neo4j_password),
        },
        "workflow": ProjectWorkflowSnapshot(
            state=WorkflowState.BLUEPRINT_GENERATED,
            approvals=ApprovalLedger.seed_release1().records,
        ).model_dump(mode="json"),
        "execution_plan": execution_plan.model_dump(mode="json"),
        "validation_evidence": validation_evidence.model_dump(mode="json"),
        "topology": _build_topology(graph),
        "network_mappings": network_mappings,
        "readiness": {
            "blockers": blocker_count,
            "warnings": warning_count,
            "findings": [
                {
                    **finding.model_dump(),
                    "target_name": node_names.get(finding.target_node_id, finding.target_node_id),
                }
                for finding in findings
            ],
        },
        "target_design": {
            "vnet": "vnet-prod",
            "subnets": ["snet-web", "snet-app", "snet-db"],
            "vm_targets": [
                {
                    "name": vm["name"],
                    "vm_size": vm["target"]["vm_size"],
                    "subnet": vm["target"]["subnet"],
                    "disk_type": vm["target"]["disk_type"],
                }
                for vm in vms
            ],
        },
        "estimate": estimate.model_dump(),
        "blueprint": blueprint.model_dump(mode="json"),
        "analysis": analysis.model_dump(),
        "artifact_href": "/artifacts/release1-assessment.md",
        "artifacts": [
            {
                "label": "Assessment summary",
                "href": "/artifacts/release1-assessment.md",
                "kind": "markdown",
            },
            {
                "label": "Migration blueprint",
                "href": "/artifacts/release1-blueprint.yaml",
                "kind": "yaml",
            },
            {
                "label": "Cutover runbook",
                "href": "/artifacts/release1-runbook.md",
                "kind": "markdown",
            },
            {
                "label": "Terraform draft",
                "href": "/artifacts/release1-main.tf",
                "kind": "terraform",
            },
        ],
    }


def build_release1_demo(
    fixture_path: Path = DEFAULT_RELEASE1_FIXTURE_PATH,
) -> Release1Demo:
    fixture = load_fixture(fixture_path)
    graph = map_fixture_to_graph(fixture)
    compute_nodes = _compute_nodes(graph)
    network_segments = _network_segments(graph)
    findings = _readiness_findings(compute_nodes)
    blocker_count = sum(finding.severity == "blocker" for finding in findings)
    warning_count = sum(finding.severity == "warning" for finding in findings)
    compute_node_names = _compute_node_names(compute_nodes)

    estimate = estimate_vmware_to_azure(
        compute_nodes=len(compute_nodes),
        storage_gb=_storage_gb(fixture),
        network_segments=len(network_segments),
        blocker_count=blocker_count,
        warning_count=warning_count,
    )
    blueprint = generate_vmware_to_azure_blueprint(
        project_id=str(fixture["project_id"]),
        application_name=APPLICATION_NAME,
        compute_node_names=compute_node_names,
    )
    analysis = run_fixture_analysis(
        compute_nodes=compute_node_names,
        blocker_count=blocker_count,
        warning_count=warning_count,
    )
    execution_plan = _build_execution_plan(fixture)
    names_by_node_id = {
        f"vm:{vm['moid']}": str(vm["name"])
        for vm in fixture["vms"]
    }
    blocked_compute_nodes = tuple(
        names_by_node_id[finding.target_node_id]
        for finding in findings
        if finding.severity == "blocker" and finding.target_node_id in names_by_node_id
    )
    validation_evidence = build_release1_validation_evidence(
        project_id=str(fixture["project_id"]),
        wave_id="wave-001",
        compute_node_names=tuple(compute_node_names),
        blocked_compute_nodes=blocked_compute_nodes,
    )

    return Release1Demo(
        graph=graph,
        graph_summary={
            "compute_nodes": len(compute_nodes),
            "network_segments": len(network_segments),
            "applications": 1 if compute_nodes else 0,
            "readiness_findings": len(findings),
        },
        readiness_findings=findings,
        estimate=estimate,
        blueprint=blueprint,
        analysis=analysis,
        execution_plan=execution_plan,
        validation_evidence=validation_evidence,
        assessment_markdown=render_assessment_markdown(
            project_name=PROJECT_NAME,
            application_name=APPLICATION_NAME,
            blockers=blocker_count,
            estimate=estimate,
        ),
        blueprint_yaml=render_blueprint_yaml(blueprint),
        runbook_markdown=render_runbook_markdown(
            project_name=PROJECT_NAME,
            blueprint=blueprint,
            blocker_count=blocker_count,
        ),
        terraform_main_tf=render_terraform_main_tf(
            blueprint=blueprint,
            location="westus2",
            resource_group_name="rg-claims-prod",
            subnet_id=_target_subnet_id("snet-app"),
        ),
        workspace=_build_workspace(
            fixture=fixture,
            graph=graph,
            graph_summary={
                "compute_nodes": len(compute_nodes),
                "network_segments": len(network_segments),
                "applications": 1 if compute_nodes else 0,
                "readiness_findings": len(findings),
            },
            findings=findings,
            estimate=estimate,
            blueprint=blueprint,
            analysis=analysis,
            execution_plan=execution_plan,
            validation_evidence=validation_evidence,
        ),
    )
