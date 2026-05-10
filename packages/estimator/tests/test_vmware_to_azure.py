from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure


def test_estimate_counts_compute_nodes_and_complexity() -> None:
    estimate = estimate_vmware_to_azure(
        compute_nodes=3,
        storage_gb=1280,
        network_segments=3,
        blocker_count=1,
        warning_count=1,
    )

    assert estimate.project_package == "assessment"
    assert estimate.asset_count == 3
    assert estimate.complexity_band == "medium"
    assert estimate.estimated_agent_usage_usd > 0
    assert estimate.base_project_fee_usd > 0
