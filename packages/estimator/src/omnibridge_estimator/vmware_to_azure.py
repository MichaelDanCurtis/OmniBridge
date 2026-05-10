from omnibridge_estimator.models import CommercialEstimate, EstimateLineItem

ASSUMPTIONS = [
    "Estimate is based on fixture/import metadata.",
    "Live vCenter discovery is not included in this MVP path.",
    "Azure Migrate is assumed as the execution backend for supported VMs.",
    "Agent usage is estimated before execution and reconciled against actual token usage.",
]
BASE_ASSESSMENT_FEE_USD = 25_000
PER_COMPUTE_NODE_ASSESSMENT_FEE_USD = 750
BASE_AGENT_TOKENS = 7_500_000
PER_COMPUTE_NODE_AGENT_TOKENS = 500_000
AGENT_TOKEN_RATE_PER_1K_USD = 0.20


def _require_non_negative(metric_name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{metric_name} must be non-negative")


def estimate_vmware_to_azure(
    compute_nodes: int,
    storage_gb: int,
    network_segments: int,
    blocker_count: int,
    warning_count: int,
) -> CommercialEstimate:
    _require_non_negative("compute_nodes", compute_nodes)
    _require_non_negative("storage_gb", storage_gb)
    _require_non_negative("network_segments", network_segments)
    _require_non_negative("blocker_count", blocker_count)
    _require_non_negative("warning_count", warning_count)

    complexity_score = (
        compute_nodes * 4
        + network_segments * 5
        + blocker_count * 15
        + warning_count * 5
        + storage_gb // 256
    )
    complexity_band = "low"
    if complexity_score >= 75:
        complexity_band = "high"
    elif complexity_score >= 30:
        complexity_band = "medium"

    project_fee_line_items = [
        EstimateLineItem(
            code="assessment_base",
            description="Release 1 migration assessment package",
            quantity=1,
            unit="project",
            unit_price_usd=BASE_ASSESSMENT_FEE_USD,
            total_usd=BASE_ASSESSMENT_FEE_USD,
        ),
        EstimateLineItem(
            code="compute_node_assessment",
            description="Per-VM discovery, readiness, target sizing, and blueprint review",
            quantity=compute_nodes,
            unit="compute_node",
            unit_price_usd=PER_COMPUTE_NODE_ASSESSMENT_FEE_USD,
            total_usd=compute_nodes * PER_COMPUTE_NODE_ASSESSMENT_FEE_USD,
        ),
    ]
    base_project_fee_usd = sum(item.total_usd for item in project_fee_line_items)
    estimated_agent_tokens = BASE_AGENT_TOKENS + compute_nodes * PER_COMPUTE_NODE_AGENT_TOKENS
    agent_usage_line_items = [
        EstimateLineItem(
            code="estimated_agent_token_usage",
            description="Estimated LangGraph agent analysis, artifact generation, and review loops",
            quantity=estimated_agent_tokens / 1000,
            unit="1k_tokens",
            unit_price_usd=AGENT_TOKEN_RATE_PER_1K_USD,
            total_usd=round((estimated_agent_tokens / 1000) * AGENT_TOKEN_RATE_PER_1K_USD),
        )
    ]

    return CommercialEstimate(
        project_package="assessment",
        pricing_model="project_fee_plus_agent_token_usage",
        asset_count=compute_nodes,
        complexity_score=complexity_score,
        complexity_band=complexity_band,
        base_project_fee_usd=base_project_fee_usd,
        estimated_agent_usage_usd=sum(item.total_usd for item in agent_usage_line_items),
        estimated_agent_tokens=estimated_agent_tokens,
        agent_token_rate_per_1k_usd=AGENT_TOKEN_RATE_PER_1K_USD,
        project_fee_line_items=project_fee_line_items,
        agent_usage_line_items=agent_usage_line_items,
        assumptions=ASSUMPTIONS,
    )
