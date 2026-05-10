import json
from pathlib import Path

from omnibridge_api.release1_demo import build_release1_demo
from omnibridge_vmware_to_azure.fixture_loader import load_fixture


def test_release1_demo_outputs_are_derived_from_fixture(tmp_path: Path) -> None:
    fixture = load_fixture(
        Path("corridors/vmware-to-azure/fixtures/acme-small-estate.json")
    )
    fixture["vms"] = fixture["vms"][:2]
    fixture_path = tmp_path / "two-vm-estate.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    demo = build_release1_demo(fixture_path)

    assert demo.graph_summary["compute_nodes"] == 2
    assert demo.estimate.asset_count == 2
    assert demo.analysis.summary.startswith("Claims Portal contains 2 compute nodes")
    assert "$26,500" in demo.assessment_markdown
