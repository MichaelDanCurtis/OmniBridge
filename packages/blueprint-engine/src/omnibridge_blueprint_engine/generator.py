from omnibridge_blueprint_engine.models import MigrationBlueprint


def generate_vmware_to_azure_blueprint(
    project_id: str,
    application_name: str,
    compute_node_names: list[str],
) -> MigrationBlueprint:
    return MigrationBlueprint(
        project_id=project_id,
        corridor="vmware-to-azure",
        application_name=application_name,
        compute_node_names=compute_node_names,
        waves=[
            {
                "name": "wave-001",
                "compute_nodes": compute_node_names,
                "execution_backend": "azure-migrate",
            }
        ],
        approval_gates=[
            "commercial_estimate_approval",
            "target_design_approval",
            "test_migration_approval",
            "cutover_approval",
        ],
    )
