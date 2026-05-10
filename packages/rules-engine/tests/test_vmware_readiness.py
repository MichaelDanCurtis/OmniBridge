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

    assert (
        findings[0].rule_id,
        findings[0].severity,
        findings[0].target_node_id,
        findings[0].message,
    ) == (
        "vmware.snapshot.exists",
        "blocker",
        "vm-1",
        "claims-db-01 has one or more VMware snapshots.",
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

    assert len(findings) == 1
    assert findings[0].rule_id == "vmware.tools.outdated"
    assert findings[0].severity == "warning"


def test_healthy_vm_creates_no_findings() -> None:
    node = GraphNode(
        id="vm-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={
            "name": "claims-web-01",
            "snapshot_count": 0,
            "tools_status": "toolsOk",
        },
    )

    findings = evaluate_vmware_vm(node)

    assert findings == []
