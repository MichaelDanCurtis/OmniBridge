from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint


def test_blueprint_contains_corridor_and_approval_gates() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-acme-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    )

    assert blueprint.corridor == "vmware-to-azure"
    assert blueprint.application_name == "Claims Portal"
    assert "commercial_estimate_approval" in blueprint.approval_gates
    assert blueprint.waves[0].name == "wave-001"


def test_blueprint_uses_full_corridor_approval_gate_order() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-acme-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01"],
    )

    assert blueprint.approval_gates == (
        "discovery_authorization",
        "commercial_estimate_approval",
        "target_design_approval",
        "test_migration_approval",
        "source_shutdown_approval",
        "cutover_approval",
        "decommission_approval",
    )


def test_blueprint_does_not_alias_input_compute_nodes() -> None:
    compute_nodes = ["claims-web-01", "claims-api-01"]

    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-acme-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=compute_nodes,
    )
    compute_nodes.append("claims-db-01")

    assert blueprint.compute_node_names == ("claims-web-01", "claims-api-01")
    assert blueprint.waves[0].compute_nodes == ("claims-web-01", "claims-api-01")


def test_blueprint_has_serialized_artifact_identity() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-acme-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01"],
    )

    artifact = blueprint.model_dump(mode="json")

    assert artifact["kind"] == "migration.blueprint"
    assert artifact["version"] == 1
    assert artifact["waves"][0]["execution_backend"] == "azure-migrate"
