from typing import Protocol

from omnibridge_blueprint_engine.models import MigrationBlueprint


class EstimateLineItemLike(Protocol):
    code: str
    description: str
    quantity: float
    unit: str
    unit_price_usd: float
    total_usd: int


class CommercialEstimateLike(Protocol):
    pricing_model: str
    base_project_fee_usd: int
    estimated_agent_usage_usd: int
    estimated_agent_tokens: int
    agent_token_rate_per_1k_usd: float
    project_fee_line_items: list[EstimateLineItemLike]
    agent_usage_line_items: list[EstimateLineItemLike]
    assumptions: list[str]


def _money(value: float) -> str:
    if float(value).is_integer():
        return f"${int(value):,}"
    return f"${value:,.2f}"


def _quantity(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _line_item(item: EstimateLineItemLike) -> str:
    return (
        f"- {item.code}: {_quantity(item.quantity)} {item.unit} x "
        f"{_money(item.unit_price_usd)} = {_money(item.total_usd)}"
    )


def render_assessment_markdown(
    project_name: str,
    application_name: str,
    blockers: int,
    estimate: CommercialEstimateLike,
) -> str:
    return "\n".join(
        [
            f"# {project_name}",
            "",
            "## Application",
            application_name,
            "",
            "## Readiness",
            f"{blockers} blocker requires consultant review.",
            "",
            "## Estimate",
            f"Pricing model: {estimate.pricing_model}",
            f"Project fee: {_money(estimate.base_project_fee_usd)}",
            f"Estimated agent usage: {_money(estimate.estimated_agent_usage_usd)}",
            (
                "Estimated tokens: "
                f"{estimate.estimated_agent_tokens:,} at "
                f"{_money(estimate.agent_token_rate_per_1k_usd)} / 1k tokens"
            ),
            "",
            "### Project Fee Line Items",
            *[_line_item(item) for item in estimate.project_fee_line_items],
            "",
            "### Agent Usage Line Items",
            *[_line_item(item) for item in estimate.agent_usage_line_items],
            "",
            "## SOW Assumptions",
            *[f"- {assumption}" for assumption in estimate.assumptions],
        ]
    )


def _yaml_list(items: tuple[str, ...], indent: str = "") -> list[str]:
    return [f"{indent}- {item}" for item in items]


def _hcl_string_list(items: tuple[str, ...]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def render_blueprint_yaml(blueprint: MigrationBlueprint) -> str:
    lines = [
        f"kind: {blueprint.kind}",
        f"version: {blueprint.version}",
        f"project_id: {blueprint.project_id}",
        f"corridor: {blueprint.corridor}",
        f"application_name: {blueprint.application_name}",
        "compute_node_names:",
        *_yaml_list(blueprint.compute_node_names, indent="  "),
        "waves:",
    ]

    for wave in blueprint.waves:
        lines.extend(
            [
                f"  - name: {wave.name}",
                f"    execution_backend: {wave.execution_backend}",
                "    compute_nodes:",
                *_yaml_list(wave.compute_nodes, indent="      "),
            ]
        )

    lines.extend(["approval_gates:", *_yaml_list(blueprint.approval_gates, indent="  ")])
    return "\n".join(lines)


def render_terraform_main_tf(
    blueprint: MigrationBlueprint,
    location: str,
    resource_group_name: str,
    subnet_id: str,
) -> str:
    return "\n".join(
        [
            f"# OmniBridge generated Terraform draft for {blueprint.application_name}",
            "# Review and harden VM images, credentials, disks, and NSGs before deployment.",
            "",
            "terraform {",
            "  required_providers {",
            "    azurerm = {",
            '      source  = "hashicorp/azurerm"',
            '      version = "~> 4.0"',
            "    }",
            "  }",
            "}",
            "",
            'provider "azurerm" {',
            "  features {}",
            "}",
            "",
            "locals {",
            f'  project_id = "{blueprint.project_id}"',
            f'  corridor = "{blueprint.corridor}"',
            f'  application_name = "{blueprint.application_name}"',
            f"  compute_node_names = {_hcl_string_list(blueprint.compute_node_names)}",
            f"  approval_gates = {_hcl_string_list(blueprint.approval_gates)}",
            "  common_tags = {",
            '    managed_by = "omnibridge"',
            "    project_id = local.project_id",
            "    corridor = local.corridor",
            "    application = local.application_name",
            "  }",
            "}",
            "",
            'resource "azurerm_resource_group" "migration" {',
            f'  name     = "{resource_group_name}"',
            f'  location = "{location}"',
            "  tags     = local.common_tags",
            "}",
            "",
            'resource "azurerm_network_interface" "vm_nic" {',
            "  for_each            = toset(local.compute_node_names)",
            '  name                = "${each.key}-nic01"',
            "  location            = azurerm_resource_group.migration.location",
            "  resource_group_name = azurerm_resource_group.migration.name",
            "",
            "  ip_configuration {",
            '    name                          = "primary"',
            f'    subnet_id                     = "{subnet_id}"',
            '    private_ip_address_allocation = "Dynamic"',
            "  }",
            "",
            "  tags = local.common_tags",
            "}",
            "",
            'resource "azurerm_linux_virtual_machine" "vm" {',
            "  for_each            = toset(local.compute_node_names)",
            '  name                = each.key',
            "  location            = azurerm_resource_group.migration.location",
            "  resource_group_name = azurerm_resource_group.migration.name",
            '  size                = "Standard_D4s_v5"',
            '  admin_username      = "omnibridgeadmin"',
            "  network_interface_ids = [",
            "    azurerm_network_interface.vm_nic[each.key].id,",
            "  ]",
            "",
            "  os_disk {",
            '    caching              = "ReadWrite"',
            '    storage_account_type = "Premium_LRS"',
            "  }",
            "",
            "  source_image_reference {",
            '    publisher = "Canonical"',
            '    offer     = "0001-com-ubuntu-server-jammy"',
            '    sku       = "22_04-lts-gen2"',
            '    version   = "latest"',
            "  }",
            "",
            "  disable_password_authentication = true",
            "",
            "  admin_ssh_key {",
            '    username   = "omnibridgeadmin"',
            '    public_key = var.admin_ssh_public_key',
            "  }",
            "",
            "  tags = merge(local.common_tags, {",
            '    migration_wave = "wave-001"',
            '    source_platform = "vmware-vcenter"',
            "  })",
            "}",
            "",
            'variable "admin_ssh_public_key" {',
            "  type        = string",
            '  description = "Temporary SSH public key used for draft Linux VM resources."',
            "  sensitive   = true",
            "}",
        ]
    )


def render_runbook_markdown(
    project_name: str,
    blueprint: MigrationBlueprint,
    blocker_count: int,
) -> str:
    compute_nodes = list(blueprint.compute_node_names)
    boot_order = list(reversed(compute_nodes))
    return "\n".join(
        [
            f"# {blueprint.application_name} Migration Runbook",
            "",
            f"Project: {project_name}",
            f"Execution backend: {blueprint.waves[0].execution_backend}",
            f"Readiness blockers: {blocker_count}",
            "",
            "## Pre-cutover",
            "1. Confirm backup completed.",
            "2. Resolve or explicitly accept all blocker findings.",
            "3. Confirm Azure network mappings and quota.",
            "4. Confirm test migration approval.",
            "",
            "## Cutover",
            "1. Obtain source shutdown approval.",
            "2. Shut down source VMs in application order:",
            *[f"   - {name}" for name in compute_nodes],
            "3. Run final delta sync through the selected migration backend.",
            "4. Create Azure VMs from replicated disks.",
            f"5. Boot Azure VMs in dependency order: {', '.join(boot_order)}.",
            "",
            "## Validation",
            "1. Confirm each VM boots successfully.",
            "2. Confirm Azure VM agent status.",
            "3. Confirm NIC, subnet, and disk attachment.",
            "4. Confirm application health checks and owner signoff.",
            "",
            "## Rollback",
            "Leave source VMs powered off but recoverable until the approved rollback window closes.",
        ]
    )
