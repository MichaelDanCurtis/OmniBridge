from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    field_validator,
)

type GraphPropertyScalar = str | int | float | bool
type GraphPropertyArray = tuple[GraphPropertyScalar, ...]
type GraphPropertyValue = GraphPropertyScalar | None | GraphPropertyArray
type GraphIdentifier = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$"),
]
type GraphLabel = GraphIdentifier
type GraphRelationshipType = GraphIdentifier


class GraphModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    @field_validator("properties", mode="after", check_fields=False)
    @classmethod
    def freeze_properties(
        cls,
        properties: Mapping[str, GraphPropertyValue],
    ) -> Mapping[str, GraphPropertyValue]:
        return MappingProxyType(dict(properties))

    @field_serializer("properties", check_fields=False)
    def serialize_properties(
        self,
        properties: Mapping[str, GraphPropertyValue],
    ) -> dict[str, GraphPropertyValue | list[GraphPropertyScalar]]:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in properties.items()
        }


class GraphNode(GraphModel):
    id: str
    project_id: str
    tenant_id: str
    labels: tuple[GraphLabel, ...] = Field(min_length=1)
    properties: Mapping[str, GraphPropertyValue] = Field(
        default_factory=dict,
        validate_default=True,
    )


class GraphEdge(GraphModel):
    id: str
    project_id: str
    tenant_id: str
    source_id: str
    target_id: str
    relationship_type: GraphRelationshipType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: tuple[str, ...] = Field(default_factory=tuple)
    properties: Mapping[str, GraphPropertyValue] = Field(
        default_factory=dict,
        validate_default=True,
    )
