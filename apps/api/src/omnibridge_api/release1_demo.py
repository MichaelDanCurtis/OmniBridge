from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omnibridge_agent_tools.models import AnalysisResult
from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis
from omnibridge_blueprint_engine.artifacts import render_assessment_markdown
from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint
from omnibridge_blueprint_engine.models import MigrationBlueprint
from omnibridge_canonical_graph.models import GraphNode
from omnibridge_estimator.models import CommercialEstimate
from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure
from omnibridge_rules_engine.models import ReadinessFinding
from omnibridge_rules_engine.vmware_readiness import evaluate_vmware_vm
from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import MappedGraph, map_fixture_to_graph


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
    assessment_markdown: str


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


def _readiness_findings(nodes: list[GraphNode]) -> list[ReadinessFinding]:
    return [
        finding
        for node in nodes
        for finding in evaluate_vmware_vm(node)
    ]


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
        assessment_markdown=render_assessment_markdown(
            project_name=PROJECT_NAME,
            application_name=APPLICATION_NAME,
            blockers=blocker_count,
            estimate_usd=estimate.base_project_fee_usd,
        ),
    )
