from fastapi.testclient import TestClient

from omnibridge_api.main import app
from omnibridge_api.routes.analysis import get_analysis_graph_repository
from omnibridge_canonical_graph.models import GraphTopologyEdge, ProjectTopology


class FakeAnalysisGraphRepository:
    def fetch_project_topology(
        self,
        project_id: str,
        tenant_id: str,
        edge_limit: int = 100,
    ) -> ProjectTopology:
        return ProjectTopology(
            node_counts={"ComputeNode": 3, "Host": 1},
            relationship_counts={"RUNS_ON": 3},
            edges=(
                GraphTopologyEdge(
                    source_id="vm:vm-103",
                    source_name="claims-db-01",
                    relationship_type="RUNS_ON",
                    target_id="host:host-101",
                    target_name="esx01",
                    evidence=("vmware.vm.host_moid",),
                ),
            ),
        )


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
    assert response.json()["analysis_source"] == "fixture"


def test_analysis_endpoint_can_use_graph_context_when_available() -> None:
    app.dependency_overrides[get_analysis_graph_repository] = lambda: FakeAnalysisGraphRepository()
    client = TestClient(app)

    try:
        response = client.get("/analysis/release1-demo?mode=graph")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_source"] == "graph"
    assert payload["graph_context_summary"].startswith(
        "Project project-release1-vmware-azure has"
    )
    assert "claims-db-01 -[RUNS_ON]-> esx01" in payload["graph_evidence_edges"]


def test_analysis_endpoint_falls_back_when_graph_mode_is_unconfigured() -> None:
    app.dependency_overrides[get_analysis_graph_repository] = lambda: None
    client = TestClient(app)

    try:
        response = client.get("/analysis/release1-demo?mode=graph")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["analysis_source"] == "fixture_fallback"


def test_artifact_endpoint_returns_markdown_assessment() -> None:
    client = TestClient(app)
    response = client.get("/artifacts/release1-assessment.md")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# OmniBridge VMware-to-Azure Assessment" in response.text
    assert "Pricing model: project_fee_plus_agent_token_usage" in response.text
    assert "assessment_base" in response.text
    assert "estimated_agent_token_usage" in response.text
    assert "9,000,000 at $0.20 / 1k tokens" in response.text


def test_artifact_endpoints_return_blueprint_and_runbook() -> None:
    client = TestClient(app)

    blueprint = client.get("/artifacts/release1-blueprint.yaml")
    runbook = client.get("/artifacts/release1-runbook.md")
    terraform = client.get("/artifacts/release1-main.tf")

    assert blueprint.status_code == 200
    assert blueprint.headers["content-type"].startswith("application/yaml")
    assert "kind: migration.blueprint" in blueprint.text
    assert "source_shutdown_approval" in blueprint.text
    assert runbook.status_code == 200
    assert runbook.headers["content-type"].startswith("text/markdown")
    assert "# Claims Portal Migration Runbook" in runbook.text
    assert "claims-db-01" in runbook.text
    assert terraform.status_code == 200
    assert terraform.headers["content-type"].startswith("text/plain")
    assert "# OmniBridge generated Terraform draft for Claims Portal" in terraform.text
    assert 'resource "azurerm_linux_virtual_machine" "vm"' in terraform.text


def test_approval_routes_return_and_update_release1_ledger() -> None:
    client = TestClient(app)

    response = client.get("/approvals/release1-demo")

    assert response.status_code == 200
    assert response.json()["state"] == "BLUEPRINT_GENERATED"
    assert response.json()["pending_approval_count"] == 6

    approve_response = client.post(
        "/approvals/release1-demo/commercial_estimate_approval/approve",
        json={
            "actor": "consultant@example.com",
            "reason": "Customer approved the estimate.",
        },
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["gate"] == "commercial_estimate_approval"
    assert approve_response.json()["status"] == "approved"


def test_execution_plan_endpoint_returns_azure_migrate_dry_run_plan() -> None:
    client = TestClient(app)

    response = client.get("/execution-plans/release1-demo")

    assert response.status_code == 200
    plan = response.json()
    assert plan["backend"] == "azure-migrate"
    assert plan["execution_mode"] == "dry_run"
    assert plan["wave_id"] == "wave-001"
    assert [operation["name"] for operation in plan["operations"]] == [
        "ensure_migrate_project",
        "register_vmware_machine",
        "register_vmware_machine",
        "register_vmware_machine",
        "start_assessment",
        "start_test_migration",
        "await_cutover_approval",
    ]
    assert plan["operations"][5]["approval_gate"] == "test_migration_approval"


def test_validation_endpoint_returns_release1_validation_evidence() -> None:
    client = TestClient(app)

    response = client.get("/validation/release1-demo")

    assert response.status_code == 200
    evidence = response.json()
    assert evidence["wave_id"] == "wave-001"
    assert evidence["summary"] == {
        "total_checks": 18,
        "pending": 12,
        "passed": 0,
        "failed": 0,
        "blocked": 6,
    }
    assert evidence["checks"][0]["check_id"] == "vm_boot"
    assert evidence["checks"][-1]["target_name"] == "claims-db-01"


def test_workspace_endpoint_returns_consultant_workspace_sections() -> None:
    client = TestClient(app)
    response = client.get("/workspace/release1-demo")

    assert response.status_code == 200
    workspace = response.json()
    assert workspace["project"]["name"] == "OmniBridge VMware-to-Azure Assessment"
    assert workspace["project"]["source"]["vcenter"] == "vcsa-prod-01"
    assert workspace["summary"]["compute_nodes"] == 3
    assert workspace["summary"]["blockers"] == 1
    assert workspace["summary"]["warnings"] == 1
    assert workspace["summary"]["total_storage_gb"] == 1280
    assert workspace["intake"]["collector"]["status"] == "not_deployed"
    assert workspace["intake"]["discovery"]["estimate_ready"] is False
    assert workspace["graph_ingest"] == {
        "source": "fixture",
        "node_count": 12,
        "edge_count": 13,
        "persisted": False,
        "neo4j_configured": False,
    }
    assert workspace["workflow"]["state"] == "BLUEPRINT_GENERATED"
    assert workspace["workflow"]["pending_approval_count"] == 6
    assert workspace["execution_plan"]["backend"] == "azure-migrate"
    assert workspace["execution_plan"]["operations"][0]["name"] == "ensure_migrate_project"
    assert workspace["execution_plan"]["operations"][5]["approval_gate"] == "test_migration_approval"
    assert workspace["validation_evidence"]["summary"]["blocked"] == 6
    assert workspace["validation_evidence"]["checks"][0]["status"] == "pending"
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
    assert workspace["artifacts"][3] == {
        "label": "Terraform draft",
        "href": "/artifacts/release1-main.tf",
        "kind": "terraform",
    }
