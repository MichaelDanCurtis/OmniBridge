from pydantic import BaseModel


class CommercialEstimate(BaseModel):
    project_package: str
    asset_count: int
    complexity_score: int
    complexity_band: str
    base_project_fee_usd: int
    estimated_agent_usage_usd: int
    assumptions: list[str]
