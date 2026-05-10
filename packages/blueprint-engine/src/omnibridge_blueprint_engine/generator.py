from omnibridge_blueprint_engine.models import MigrationBlueprint, MigrationWave


VMWARE_TO_AZURE_APPROVAL_GATES = (
    "discovery_authorization",
    "commercial_estimate_approval",
    "target_design_approval",
    "test_migration_approval",
    "source_shutdown_approval",
    "cutover_approval",
    "decommission_approval",
)


def generate_vmware_to_azure_blueprint(
    project_id: str,
    application_name: str,
    compute_node_names: list[str],
) -> MigrationBlueprint:
    compute_nodes = tuple(compute_node_names)
    return MigrationBlueprint(
        project_id=project_id,
        corridor="vmware-to-azure",
        application_name=application_name,
        compute_node_names=compute_nodes,
        waves=(
            MigrationWave(
                name="wave-001",
                compute_nodes=compute_nodes,
                execution_backend="azure-migrate",
            ),
        ),
        approval_gates=VMWARE_TO_AZURE_APPROVAL_GATES,
    )
