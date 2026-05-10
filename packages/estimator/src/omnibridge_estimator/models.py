from pydantic import BaseModel


class EstimateLineItem(BaseModel):
    code: str
    description: str
    quantity: float
    unit: str
    unit_price_usd: float
    total_usd: int


class CommercialEstimate(BaseModel):
    project_package: str
    pricing_model: str
    asset_count: int
    complexity_score: int
    complexity_band: str
    base_project_fee_usd: int
    estimated_agent_usage_usd: int
    estimated_agent_tokens: int
    agent_token_rate_per_1k_usd: float
    project_fee_line_items: list[EstimateLineItem]
    agent_usage_line_items: list[EstimateLineItem]
    assumptions: list[str]
