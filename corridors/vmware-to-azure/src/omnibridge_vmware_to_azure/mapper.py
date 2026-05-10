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

    for cluster in fixture["clusters"]:
        nodes.append(
            GraphNode(
                id=f"cluster:{cluster['moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["Cluster", "VMwareCluster"],
                properties={"name": cluster["name"]},
            )
        )

    for host in fixture["hosts"]:
        host_id = f"host:{host['moid']}"
        cluster_id = f"cluster:{host['cluster_moid']}"
        nodes.append(
            GraphNode(
                id=host_id,
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["Host", "VMwareHost"],
                properties={"name": host["name"]},
            )
        )
        edges.append(
            GraphEdge(
                id=f"{host_id}:belongs_to:{host['cluster_moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                source_id=host_id,
                target_id=cluster_id,
                relationship_type="BELONGS_TO",
                evidence=["vmware.host.cluster_moid"],
            )
        )

    for datastore in fixture["datastores"]:
        nodes.append(
            GraphNode(
                id=f"datastore:{datastore['moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["Datastore", "VMwareDatastore"],
                properties={
                    "name": datastore["name"],
                    "capacity_gb": datastore["capacity_gb"],
                },
            )
        )

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

        edges.append(
            GraphEdge(
                id=f"{vm_id}:runs_on:{vm['host_moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                source_id=vm_id,
                target_id=f"host:{vm['host_moid']}",
                relationship_type="RUNS_ON",
                evidence=["vmware.vm.host_moid"],
            )
        )

        for disk_index, disk in enumerate(vm["disks"]):
            volume_id = f"volume:{vm['moid']}:{disk_index}"
            datastore_id = f"datastore:{disk['datastore_moid']}"
            nodes.append(
                GraphNode(
                    id=volume_id,
                    project_id=project_id,
                    tenant_id=tenant_id,
                    labels=["StorageVolume", "VMwareVirtualDisk"],
                    properties={
                        "name": f"{vm['name']}-disk-{disk_index}",
                        "size_gb": disk["size_gb"],
                        "disk_index": disk_index,
                    },
                )
            )
            edges.append(
                GraphEdge(
                    id=f"{vm_id}:has_volume:{disk_index}",
                    project_id=project_id,
                    tenant_id=tenant_id,
                    source_id=vm_id,
                    target_id=volume_id,
                    relationship_type="HAS_VOLUME",
                    evidence=["vmware.vm.disks"],
                )
            )
            edges.append(
                GraphEdge(
                    id=f"{volume_id}:uses_datastore:{disk['datastore_moid']}",
                    project_id=project_id,
                    tenant_id=tenant_id,
                    source_id=volume_id,
                    target_id=datastore_id,
                    relationship_type="USES_DATASTORE",
                    evidence=["vmware.disk.datastore_moid"],
                )
            )

    return MappedGraph(nodes=nodes, edges=edges)
