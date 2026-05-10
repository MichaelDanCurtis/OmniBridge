import pytest

from omnibridge_azure_migrate_adapter.operations import (
    AzureMigrateMachineRef,
    AzureMigrateOperationPlanner,
    AzureMigrateProjectRef,
)


def test_planner_builds_dry_run_agentless_vmware_wave_operations() -> None:
    planner = AzureMigrateOperationPlanner()
    plan = planner.plan_agentless_vmware_wave(
        project=AzureMigrateProjectRef(
            subscription_id="sub-123",
            resource_group="rg-migrate",
            project_name="omni-acme",
            region="westus2",
        ),
        wave_id="wave-001",
        source_machines=(
            AzureMigrateMachineRef(
                vm_moid="vm-101",
                vm_name="claims-web-01",
                target_vm_size="Standard_D4s_v5",
                target_subnet_id="/subscriptions/sub-123/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-prod/subnets/snet-web",
            ),
        ),
    )

    assert plan.backend == "azure-migrate"
    assert plan.execution_mode == "dry_run"
    assert [operation.name for operation in plan.operations] == [
        "ensure_migrate_project",
        "register_vmware_machine",
        "start_assessment",
        "start_test_migration",
        "await_cutover_approval",
    ]
    assert all(operation.execution_mode == "dry_run" for operation in plan.operations)
    assert plan.operations[1].payload["vm_name"] == "claims-web-01"
    assert plan.operations[3].approval_gate == "test_migration_approval"
    assert plan.operations[4].approval_gate == "cutover_approval"


def test_planner_rejects_empty_wave() -> None:
    planner = AzureMigrateOperationPlanner()

    with pytest.raises(ValueError, match="at least one source machine"):
        planner.plan_agentless_vmware_wave(
            project=AzureMigrateProjectRef(
                subscription_id="sub-123",
                resource_group="rg-migrate",
                project_name="omni-acme",
                region="westus2",
            ),
            wave_id="wave-001",
            source_machines=(),
        )
