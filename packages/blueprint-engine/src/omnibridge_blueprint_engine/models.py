from typing import Literal

from pydantic import BaseModel, ConfigDict


class MigrationWave(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    compute_nodes: tuple[str, ...]
    execution_backend: str


class MigrationBlueprint(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["migration.blueprint"] = "migration.blueprint"
    version: int = 1
    project_id: str
    corridor: str
    application_name: str
    compute_node_names: tuple[str, ...]
    waves: tuple[MigrationWave, ...]
    approval_gates: tuple[str, ...]
