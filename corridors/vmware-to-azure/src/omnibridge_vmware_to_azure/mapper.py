from dataclasses import dataclass
from typing import Any

from omnibridge_canonical_graph.models import GraphEdge, GraphNode


@dataclass(frozen=True)
class MappedGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


def map_fixture_to_graph(fixture: dict[str, Any]) -> MappedGraph:
    project_id = fixture["project_id"]
    tenant_id = fixture["tenant_id"]
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for network in fixture["networks"]:
        nodes.append(
            GraphNode(
                id=f"network:{network['moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["NetworkSegment", "VMwarePortGroup"],
                properties={
                    "name": network["name"],
                    "vlan": network["vlan"],
                },
            )
        )

    for vm in fixture["vms"]:
        vm_id = f"vm:{vm['moid']}"
        nodes.append(
            GraphNode(
                id=vm_id,
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["ComputeNode", "VMwareVirtualMachine"],
                properties={
                    "name": vm["name"],
                    "cpu": vm["cpu"],
                    "memory_mb": vm["memory_mb"],
                    "guest_os": vm["guest_os"],
                    "tools_status": vm["tools_status"],
                    "snapshot_count": vm["snapshot_count"],
                },
            )
        )

        for nic_index, nic in enumerate(vm["nics"]):
            network_moid = nic["network_moid"]
            edges.append(
                GraphEdge(
                    id=f"{vm_id}:connected_to:{network_moid}:{nic_index}",
                    project_id=project_id,
                    tenant_id=tenant_id,
                    source_id=vm_id,
                    target_id=f"network:{network_moid}",
                    relationship_type="CONNECTED_TO",
                    evidence=["vmware.vm.nic.network_moid"],
                    properties={"ip": nic["ip"]},
                )
            )

    return MappedGraph(nodes=nodes, edges=edges)
