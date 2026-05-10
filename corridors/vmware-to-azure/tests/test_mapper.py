from pathlib import Path

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


FIXTURE_PATH = Path("corridors/vmware-to-azure/fixtures/acme-small-estate.json")


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
