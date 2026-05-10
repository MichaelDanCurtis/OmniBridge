from omnibridge_canonical_graph.models import GraphNode
from omnibridge_rules_engine.vmware_readiness import evaluate_vmware_vm


def test_snapshot_count_creates_blocker() -> None:
    node = GraphNode(
        id="vm-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={
            "name": "claims-db-01",
            "snapshot_count": 1,
            "tools_status": "toolsOld",
        },
    )

    findings = evaluate_vmware_vm(node)

    assert any(
        finding.rule_id == "vmware.snapshot.exists"
        and finding.severity == "blocker"
        for finding in findings
    )


def test_tools_old_creates_warning() -> None:
    node = GraphNode(
        id="vm-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={
            "name": "claims-db-01",
            "snapshot_count": 0,
            "tools_status": "toolsOld",
        },
    )

    findings = evaluate_vmware_vm(node)

    assert any(
        finding.rule_id == "vmware.tools.outdated" for finding in findings
    )
