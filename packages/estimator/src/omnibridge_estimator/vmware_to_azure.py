from omnibridge_estimator.models import CommercialEstimate

ASSUMPTIONS = [
    "Estimate is based on fixture/import metadata.",
    "Live vCenter discovery is not included in this MVP path.",
    "Azure Migrate is assumed as the execution backend for supported VMs.",
]


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

    return CommercialEstimate(
        project_package="assessment",
        asset_count=compute_nodes,
        complexity_score=complexity_score,
        complexity_band=complexity_band,
        base_project_fee_usd=25000 + compute_nodes * 750,
        estimated_agent_usage_usd=1500 + compute_nodes * 100,
        assumptions=ASSUMPTIONS,
    )
