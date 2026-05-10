from omnibridge_canonical_graph.models import GraphNode

from omnibridge_rules_engine.models import ReadinessFinding


def evaluate_vmware_vm(node: GraphNode) -> list[ReadinessFinding]:
    name = str(node.properties.get("name", node.id))
    findings: list[ReadinessFinding] = []

    if int(node.properties.get("snapshot_count", 0)) > 0:
        findings.append(
            ReadinessFinding(
                rule_id="vmware.snapshot.exists",
                severity="blocker",
                target_node_id=node.id,
                message=f"{name} has one or more VMware snapshots.",
            )
        )

    if node.properties.get("tools_status") != "toolsOk":
        findings.append(
            ReadinessFinding(
                rule_id="vmware.tools.outdated",
                severity="warning",
                target_node_id=node.id,
                message=f"{name} does not report healthy VMware Tools status.",
            )
        )

    return findings
