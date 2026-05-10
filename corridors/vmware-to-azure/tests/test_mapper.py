from pathlib import Path

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "acme-small-estate.json"
)


def test_fixture_maps_vms_to_compute_nodes() -> None:
    fixture = load_fixture(FIXTURE_PATH)

    graph = map_fixture_to_graph(fixture)

    compute_node_names = {
        node.properties["name"]
        for node in graph.nodes
        if "ComputeNode" in node.labels
    }
    assert compute_node_names == {
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    }


def test_fixture_maps_vm_network_relationships() -> None:
    fixture = load_fixture(FIXTURE_PATH)

    graph = map_fixture_to_graph(fixture)

    connected_edges = [
        edge for edge in graph.edges if edge.relationship_type == "CONNECTED_TO"
    ]
    assert len(connected_edges) == 3


def test_fixture_maps_host_cluster_and_storage_topology() -> None:
    fixture = load_fixture(FIXTURE_PATH)

    graph = map_fixture_to_graph(fixture)

    label_names = {
        label: {
            node.properties["name"]
            for node in graph.nodes
            if label in node.labels
        }
        for label in ["Cluster", "Host", "Datastore", "StorageVolume"]
    }
    assert label_names["Cluster"] == {"Prod-Cluster"}
    assert label_names["Host"] == {"esx01"}
    assert label_names["Datastore"] == {"datastore-prod-01"}
    assert label_names["StorageVolume"] == {
        "claims-web-01-disk-0",
        "claims-api-01-disk-0",
        "claims-db-01-disk-0",
    }

    relationship_counts = {
        relationship_type: len(
            [
                edge
                for edge in graph.edges
                if edge.relationship_type == relationship_type
            ]
        )
        for relationship_type in [
            "BELONGS_TO",
            "RUNS_ON",
            "HAS_VOLUME",
            "USES_DATASTORE",
        ]
    }
    assert relationship_counts == {
        "BELONGS_TO": 1,
        "RUNS_ON": 3,
        "HAS_VOLUME": 3,
        "USES_DATASTORE": 3,
    }
    assert any(
        edge.source_id == "vm:vm-103"
        and edge.target_id == "host:host-101"
        and edge.relationship_type == "RUNS_ON"
        for edge in graph.edges
    )
