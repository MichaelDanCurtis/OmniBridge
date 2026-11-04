from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ExecutionMode = Literal["dry_run"]


class AzureMigrateProjectRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    subscription_id: str
    resource_group: str
    project_name: str
    region: str


class AzureMigrateMachineRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    vm_moid: str
    vm_name: str
    target_vm_size: str
    target_subnet_id: str


class AzureMigrateOperation(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    execution_mode: ExecutionMode = "dry_run"
    approval_required: bool = False
    approval_gate: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)


class AzureMigrateOperationPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    backend: Literal["azure-migrate"] = "azure-migrate"
    execution_mode: ExecutionMode = "dry_run"
    wave_id: str
    operations: tuple[AzureMigrateOperation, ...]


class AzureMigrateOperationPlanner:
    def plan_agentless_vmware_wave(
        self,
        *,
        project: AzureMigrateProjectRef,
        wave_id: str,
        source_machines: Sequence[AzureMigrateMachineRef],
    ) -> AzureMigrateOperationPlan:
        if not source_machines:
            raise ValueError("Azure Migrate wave requires at least one source machine")

        operations = [
            AzureMigrateOperation(
                name="ensure_migrate_project",
                payload={
                    "subscription_id": project.subscription_id,
                    "resource_group": project.resource_group,
                    "project_name": project.project_name,
                    "region": project.region,
                },
            ),
            *(
                AzureMigrateOperation(
                    name="register_vmware_machine",
                    payload={
                        "project_name": project.project_name,
                        "vm_moid": machine.vm_moid,
                        "vm_name": machine.vm_name,
                        "target_vm_size": machine.target_vm_size,
                        "target_subnet_id": machine.target_subnet_id,
                    },
                )
                for machine in source_machines
            ),
            AzureMigrateOperation(
                name="start_assessment",
                payload={
                    "project_name": project.project_name,
                    "wave_id": wave_id,
                    "vm_moids": tuple(machine.vm_moid for machine in source_machines),
                },
            ),
            AzureMigrateOperation(
                name="start_test_migration",
                approval_required=True,
                approval_gate="test_migration_approval",
                payload={
                    "project_name": project.project_name,
                    "wave_id": wave_id,
                    "vm_moids": tuple(machine.vm_moid for machine in source_machines),
                },
            ),
            AzureMigrateOperation(
                name="await_cutover_approval",
                approval_required=True,
                approval_gate="cutover_approval",
                payload={
                    "project_name": project.project_name,
                    "wave_id": wave_id,
                },
            ),
        ]

        return AzureMigrateOperationPlan(
            wave_id=wave_id,
            operations=tuple(operations),
        )
