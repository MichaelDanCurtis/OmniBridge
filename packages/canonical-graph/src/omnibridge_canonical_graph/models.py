from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    labels: list[str]
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float = 1.0
    evidence: list[str] = Field(default_factory=list)
    properties: dict[str, object] = Field(default_factory=dict)
