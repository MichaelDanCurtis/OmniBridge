from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

type GraphPropertyScalar = str | int | float | bool
type GraphPropertyValue = GraphPropertyScalar | None | list[GraphPropertyScalar]
type GraphIdentifier = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$"),
]
type GraphLabel = GraphIdentifier
type GraphRelationshipType = GraphIdentifier


class GraphNode(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    labels: list[GraphLabel] = Field(min_length=1)
    properties: dict[str, GraphPropertyValue] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    source_id: str
    target_id: str
    relationship_type: GraphRelationshipType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    properties: dict[str, GraphPropertyValue] = Field(default_factory=dict)
