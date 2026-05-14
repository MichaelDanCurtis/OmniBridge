from types import SimpleNamespace

from omnibridge_blueprint_engine.artifacts import (
    render_assessment_markdown,
    render_blueprint_yaml,
    render_terraform_main_tf,
    render_runbook_markdown,
)
from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint


def test_render_assessment_markdown_contains_project_and_decisions() -> None:
    estimate = SimpleNamespace(
        pricing_model="project_fee_plus_agent_token_usage",
        base_project_fee_usd=27250,
        estimated_agent_usage_usd=1800,
        estimated_agent_tokens=9_000_000,
        agent_token_rate_per_1k_usd=0.20,
        project_fee_line_items=[
            SimpleNamespace(
                code="assessment_base",
                description="Release 1 migration assessment package",
                quantity=1,
                unit="project",
                unit_price_usd=25000,
                total_usd=25000,
            ),
            SimpleNamespace(
                code="compute_node_assessment",
                description="Per-VM discovery, readiness, target sizing, and blueprint review",
                quantity=3,
                unit="compute_node",
                unit_price_usd=750,
                total_usd=2250,
            ),
        ],
        agent_usage_line_items=[
            SimpleNamespace(
                code="estimated_agent_token_usage",
                description="Estimated LangGraph agent analysis",
                quantity=9000,
                unit="1k_tokens",
                unit_price_usd=0.20,
                total_usd=1800,
            )
        ],
        assumptions=[
            "Estimate is based on fixture/import metadata.",
            "Agent usage is estimated before execution and reconciled against actual token usage.",
        ],
    )
    markdown = render_assessment_markdown(
        project_name="OmniBridge VMware-to-Azure Assessment",
        application_name="Claims Portal",
        blockers=1,
        estimate=estimate,
    )

    assert "# OmniBridge VMware-to-Azure Assessment" in markdown
    assert "Claims Portal" in markdown
    assert "1 blocker" in markdown
    assert "$27,250" in markdown
    assert "project_fee_plus_agent_token_usage" in markdown
    assert "assessment_base" in markdown
    assert "compute_node_assessment" in markdown
    assert "9,000,000 at $0.20 / 1k tokens" in markdown
    assert "estimated_agent_token_usage" in markdown
    assert "Agent usage is estimated before execution" in markdown


def test_render_blueprint_yaml_contains_waves_and_approval_gates() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-release1-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    )

    yaml = render_blueprint_yaml(blueprint)

    assert "kind: migration.blueprint" in yaml
    assert "application_name: Claims Portal" in yaml
    assert "  - claims-db-01" in yaml
    assert "execution_backend: azure-migrate" in yaml
    assert "  - source_shutdown_approval" in yaml


def test_render_runbook_markdown_contains_cutover_and_validation_steps() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-release1-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    )

    markdown = render_runbook_markdown(
        project_name="OmniBridge VMware-to-Azure Assessment",
        blueprint=blueprint,
        blocker_count=1,
    )

    assert "# Claims Portal Migration Runbook" in markdown
    assert "## Pre-cutover" in markdown
    assert "claims-db-01" in markdown
    assert "## Cutover" in markdown
    assert "## Validation" in markdown


def test_render_terraform_main_tf_contains_release1_vm_draft() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-release1-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    )

    terraform = render_terraform_main_tf(
        blueprint=blueprint,
        location="westus2",
        resource_group_name="rg-claims-prod",
        subnet_id="/subscriptions/sub-omnibridge-prod/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-prod/subnets/snet-app",
    )

    assert '# OmniBridge generated Terraform draft for Claims Portal' in terraform
    assert 'required_providers' in terraform
    assert 'resource "azurerm_resource_group" "migration"' in terraform
    assert 'resource "azurerm_network_interface" "vm_nic"' in terraform
    assert 'resource "azurerm_linux_virtual_machine" "vm"' in terraform
    assert '"claims-db-01"' in terraform
    assert '"source_shutdown_approval"' in terraform
    assert '"decommission_approval"' in terraform
