from fastapi import APIRouter

from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint


router = APIRouter(prefix="/blueprints", tags=["blueprints"])


@router.get("/release1-demo")
def release1_demo_blueprint() -> dict[str, object]:
    return generate_vmware_to_azure_blueprint(
        project_id="project-acme-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    ).model_dump(mode="json")
