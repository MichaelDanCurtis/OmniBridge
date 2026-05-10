from pydantic import BaseModel


class AnalysisResult(BaseModel):
    summary: str
    requires_consultant_review: bool
    decision_points: list[str]
