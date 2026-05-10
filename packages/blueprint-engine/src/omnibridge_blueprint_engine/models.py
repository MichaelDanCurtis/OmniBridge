from pydantic import BaseModel


class MigrationBlueprint(BaseModel):
    project_id: str
    corridor: str
    application_name: str
    compute_node_names: list[str]
    waves: list[dict[str, object]]
    approval_gates: list[str]
