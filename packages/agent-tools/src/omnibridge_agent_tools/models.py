from pydantic import BaseModel


class AnalysisResult(BaseModel):
    summary: str
    requires_consultant_review: bool
    decision_points: list[str]


class GraphTopologyContext(BaseModel):
    summary: str
    node_counts: dict[str, int]
    relationship_counts: dict[str, int]
    evidence_edges: list[str]
