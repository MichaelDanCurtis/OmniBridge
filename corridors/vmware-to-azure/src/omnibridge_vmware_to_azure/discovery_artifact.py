from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


class DiscoveryModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class SourceMetadata(DiscoveryModel):
    project_id: str
    tenant_id: str
    source_system: Literal["vmware"] = "vmware"


class ClusterInventoryItem(DiscoveryModel):
    moid: str
    name: str


class HostInventoryItem(DiscoveryModel):
    moid: str
    name: str
    cluster_moid: str


class DatastoreInventoryItem(DiscoveryModel):
    moid: str
    name: str
    capacity_gb: int


class NetworkInventoryItem(DiscoveryModel):
    moid: str
    name: str
    vlan: int


class VmNicInventoryItem(DiscoveryModel):
    network_moid: str
    ip: str


class VmDiskInventoryItem(DiscoveryModel):
    datastore_moid: str
    size_gb: int


class VmInventoryItem(DiscoveryModel):
    moid: str
    name: str
    cluster_moid: str
    host_moid: str
    cpu: int
    memory_mb: int
    guest_os: str
    tools_status: str
    snapshot_count: int
    nics: tuple[VmNicInventoryItem, ...] = Field(default_factory=tuple)
    disks: tuple[VmDiskInventoryItem, ...] = Field(default_factory=tuple)


class DiscoveryInventory(DiscoveryModel):
    clusters: tuple[ClusterInventoryItem, ...] = Field(default_factory=tuple)
    hosts: tuple[HostInventoryItem, ...] = Field(default_factory=tuple)
    datastores: tuple[DatastoreInventoryItem, ...] = Field(default_factory=tuple)
    networks: tuple[NetworkInventoryItem, ...] = Field(default_factory=tuple)
    vms: tuple[VmInventoryItem, ...] = Field(default_factory=tuple)


class DiscoveryRelationship(DiscoveryModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    evidence: tuple[str, ...] = Field(default_factory=tuple)


class DiscoverySummary(DiscoveryModel):
    compute_nodes: int
    network_segments: int
    graph_nodes: int
    graph_edges: int


class DiscoveryEvent(DiscoveryModel):
    status: Literal["started", "running", "completed", "failed"]
    message: str
    sequence: int


class DiscoveryArtifact(DiscoveryModel):
    source: SourceMetadata
    vcenter: str
    datacenter: str
    inventory: DiscoveryInventory
    relationships: tuple[DiscoveryRelationship, ...] = Field(default_factory=tuple)
    summary: DiscoverySummary
    events: tuple[DiscoveryEvent, ...] = Field(default_factory=tuple)
    source_mode: Literal["fixture", "collector", "vcenter"]
    fixture_path: str | None = None


def build_discovery_artifact_from_release1_fixture(fixture_path: Path) -> DiscoveryArtifact:
    fixture = load_fixture(fixture_path)
    return build_discovery_artifact_from_fixture_payload(
        fixture,
        source_mode="fixture",
        fixture_path=fixture_path,
    )


def build_discovery_artifact_from_fixture_payload(
    fixture: dict[str, Any],
    *,
    source_mode: Literal["fixture", "collector", "vcenter"],
    fixture_path: Path | None = None,
) -> DiscoveryArtifact:
    graph = map_fixture_to_graph(fixture)

    relationships = tuple(
        DiscoveryRelationship(
            id=edge.id,
            source_id=edge.source_id,
            target_id=edge.target_id,
            relationship_type=edge.relationship_type,
            evidence=edge.evidence,
        )
        for edge in graph.edges
    )

    return DiscoveryArtifact(
        source=SourceMetadata(
            project_id=fixture["project_id"],
            tenant_id=fixture["tenant_id"],
        ),
        vcenter=fixture["vcenter"],
        datacenter=fixture["datacenter"],
        inventory=DiscoveryInventory(
            clusters=tuple(
                ClusterInventoryItem.model_validate(cluster)
                for cluster in fixture["clusters"]
            ),
            hosts=tuple(HostInventoryItem.model_validate(host) for host in fixture["hosts"]),
            datastores=tuple(
                DatastoreInventoryItem.model_validate(datastore)
                for datastore in fixture["datastores"]
            ),
            networks=tuple(
                NetworkInventoryItem.model_validate(network)
                for network in fixture["networks"]
            ),
            vms=tuple(VmInventoryItem.model_validate(vm) for vm in fixture["vms"]),
        ),
        relationships=relationships,
        summary=DiscoverySummary(
            compute_nodes=len(fixture["vms"]),
            network_segments=len(fixture["networks"]),
            graph_nodes=len(graph.nodes),
            graph_edges=len(graph.edges),
        ),
        events=(
            DiscoveryEvent(
                sequence=1,
                status="started",
                message="Started VMware discovery from release1 fixture.",
            ),
            DiscoveryEvent(
                sequence=2,
                status="running",
                message="Loaded VMware inventory sections from fixture.",
            ),
            DiscoveryEvent(
                sequence=3,
                status="running",
                message="Mapped VMware inventory to canonical graph relationships.",
            ),
            DiscoveryEvent(
                sequence=4,
                status="completed",
                message="Completed VMware discovery artifact build.",
            ),
        ),
        source_mode=source_mode,
        fixture_path=str(fixture_path) if fixture_path is not None else None,
    )
