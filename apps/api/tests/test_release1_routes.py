from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_estimate_endpoint_returns_commercial_estimate() -> None:
    client = TestClient(app)
    response = client.get("/estimates/release1-demo")
    assert response.status_code == 200
    assert response.json()["project_package"] == "assessment"


def test_blueprint_endpoint_returns_vmware_to_azure_blueprint() -> None:
    client = TestClient(app)
    response = client.get("/blueprints/release1-demo")
    assert response.status_code == 200
    blueprint = response.json()
    assert blueprint["corridor"] == "vmware-to-azure"
    assert blueprint["compute_node_names"] == [
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    ]
    assert blueprint["waves"][0]["compute_nodes"] == [
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    ]
    assert "source_shutdown_approval" in blueprint["approval_gates"]


def test_analysis_endpoint_returns_decision_points() -> None:
    client = TestClient(app)
    response = client.get("/analysis/release1-demo")
    assert response.status_code == 200
    assert response.json()["requires_consultant_review"] is True


def test_artifact_endpoint_returns_markdown_assessment() -> None:
    client = TestClient(app)
    response = client.get("/artifacts/release1-assessment.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# ACME VMware-to-Azure Assessment" in response.text
    assert "Pricing model: project_fee_plus_agent_token_usage" in response.text
    assert "assessment_base" in response.text
    assert "estimated_agent_token_usage" in response.text
    assert "9,000,000 at $0.20 / 1k tokens" in response.text


def test_artifact_endpoints_return_blueprint_and_runbook() -> None:
    client = TestClient(app)

    blueprint = client.get("/artifacts/release1-blueprint.yaml")
    runbook = client.get("/artifacts/release1-runbook.md")

    assert blueprint.status_code == 200
    assert blueprint.headers["content-type"].startswith("application/yaml")
    assert "kind: migration.blueprint" in blueprint.text
    assert "source_shutdown_approval" in blueprint.text
    assert runbook.status_code == 200
    assert runbook.headers["content-type"].startswith("text/markdown")
    assert "# Claims Portal Migration Runbook" in runbook.text
    assert "claims-db-01" in runbook.text


def test_workspace_endpoint_returns_consultant_workspace_sections() -> None:
    client = TestClient(app)
    response = client.get("/workspace/release1-demo")

    assert response.status_code == 200
    workspace = response.json()
    assert workspace["project"]["name"] == "ACME VMware-to-Azure Assessment"
    assert workspace["project"]["source"]["vcenter"] == "vcsa-prod-01"
    assert workspace["summary"]["compute_nodes"] == 3
    assert workspace["summary"]["blockers"] == 1
    assert workspace["summary"]["warnings"] == 1
    assert workspace["summary"]["total_storage_gb"] == 1280
    assert workspace["topology"]["node_counts"]["ComputeNode"] == 3
    assert workspace["topology"]["node_counts"]["Host"] == 1
    assert workspace["topology"]["relationship_counts"]["RUNS_ON"] == 3
    assert workspace["topology"]["relationship_counts"]["HAS_VOLUME"] == 3
    assert workspace["topology"]["edges"][0]["source_name"] == "esx01"
    assert workspace["estimate"]["pricing_model"] == "project_fee_plus_agent_token_usage"
    assert workspace["estimate"]["project_fee_line_items"][0]["code"] == "assessment_base"
    assert workspace["estimate"]["project_fee_line_items"][1]["total_usd"] == 2250
    assert workspace["estimate"]["estimated_agent_tokens"] == 9_000_000
    assert workspace["readiness"]["findings"][0]["target_name"] == "claims-db-01"
    assert workspace["inventory"]["vms"][2]["target"]["vm_size"] == "Standard_D8s_v5"
    assert workspace["network_mappings"][2] == {
        "source_portgroup": "dvpg-db-prod",
        "vlan": 122,
        "target_vnet": "vnet-prod",
        "target_subnet": "snet-db",
        "security_intent": "Allow SQL traffic from app tier only.",
    }
    assert workspace["artifact_href"] == "/artifacts/release1-assessment.md"
    assert workspace["artifacts"][1] == {
        "label": "Migration blueprint",
        "href": "/artifacts/release1-blueprint.yaml",
        "kind": "yaml",
    }
