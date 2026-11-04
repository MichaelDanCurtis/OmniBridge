from pathlib import Path

from omnibridge_vmware_to_azure.discovery_artifact import (
    DiscoveryArtifact,
    build_discovery_artifact_from_fixture_payload,
    build_discovery_artifact_from_release1_fixture,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "release1-small-estate.json"
)


def test_release1_fixture_builds_canonical_discovery_artifact() -> None:
    artifact = build_discovery_artifact_from_release1_fixture(FIXTURE_PATH)

    assert isinstance(artifact, DiscoveryArtifact)
    assert artifact.source_mode == "fixture"
    assert artifact.fixture_path == str(FIXTURE_PATH)
    assert artifact.source.project_id == "project-release1-vmware-azure"
    assert artifact.source.tenant_id == "tenant-omnibridge-demo"
    assert artifact.vcenter == "vcsa-prod-01"
    assert artifact.datacenter == "DC1"

    assert artifact.summary.compute_nodes == 3
    assert artifact.summary.network_segments == 3
    assert artifact.summary.graph_nodes == 12
    assert artifact.summary.graph_edges == 13

    assert {vm.name for vm in artifact.inventory.vms} == {
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    }
    assert {network.name for network in artifact.inventory.networks} == {
        "dvpg-web-prod",
        "dvpg-app-prod",
        "dvpg-db-prod",
    }
    assert {datastore.name for datastore in artifact.inventory.datastores} == {
        "datastore-prod-01",
    }

    assert artifact.relationships
    assert any(
        relationship.source_id == "vm:vm-103"
        and relationship.target_id == "host:host-101"
        and relationship.relationship_type == "RUNS_ON"
        for relationship in artifact.relationships
    )
    assert any(event.status == "completed" for event in artifact.events)


def test_payload_builder_supports_collector_sourced_discovery() -> None:
    fixture = {
        "project_id": "project-release1-vmware-azure",
        "tenant_id": "tenant-omnibridge-demo",
        "vcenter": "vcsa-prod-01",
        "datacenter": "DC1",
        "clusters": [{"moid": "domain-c1", "name": "Prod-Cluster"}],
        "hosts": [
            {"moid": "host-101", "name": "esx01", "cluster_moid": "domain-c1"}
        ],
        "datastores": [
            {"moid": "datastore-11", "name": "datastore-prod-01", "capacity_gb": 2048}
        ],
        "networks": [
            {"moid": "dvportgroup-120", "name": "dvpg-web-prod", "vlan": 120}
        ],
        "vms": [
            {
                "moid": "vm-101",
                "name": "claims-web-01",
                "cluster_moid": "domain-c1",
                "host_moid": "host-101",
                "cpu": 2,
                "memory_mb": 8192,
                "guest_os": "ubuntuLinux64Guest",
                "tools_status": "toolsOk",
                "snapshot_count": 0,
                "nics": [{"network_moid": "dvportgroup-120", "ip": "10.20.10.10"}],
                "disks": [{"datastore_moid": "datastore-11", "size_gb": 128}],
            }
        ],
    }

    artifact = build_discovery_artifact_from_fixture_payload(
        fixture,
        source_mode="collector",
    )

    assert artifact.source_mode == "collector"
    assert artifact.fixture_path is None
    assert artifact.summary.compute_nodes == 1
    assert artifact.summary.network_segments == 1
    assert artifact.inventory.vms[0].name == "claims-web-01"
