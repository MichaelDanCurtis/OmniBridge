from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    summary: str
    requires_consultant_review: bool
    decision_points: list[str]
    analysis_source: str = "fixture"
    graph_context_summary: str | None = None
    graph_evidence_edges: list[str] = Field(default_factory=list)


class GraphTopologyContext(BaseModel):
    summary: str
    node_counts: dict[str, int]
    relationship_counts: dict[str, int]
    evidence_edges: list[str]
