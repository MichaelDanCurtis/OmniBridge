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
    assert blueprint.waves[0]["name"] == "wave-001"
