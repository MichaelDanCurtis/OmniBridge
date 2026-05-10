import pytest

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


def test_estimate_rejects_negative_inputs() -> None:
    with pytest.raises(ValueError, match="compute_nodes must be non-negative"):
        estimate_vmware_to_azure(
            compute_nodes=-1,
            storage_gb=1280,
            network_segments=3,
            blocker_count=1,
            warning_count=1,
        )


@pytest.mark.parametrize(
    ("storage_gb", "expected_band"),
    [
        (7424, "low"),
        (7680, "medium"),
        (18944, "medium"),
        (19200, "high"),
    ],
)
def test_estimate_complexity_band_boundaries(
    storage_gb: int,
    expected_band: str,
) -> None:
    estimate = estimate_vmware_to_azure(
        compute_nodes=0,
        storage_gb=storage_gb,
        network_segments=0,
        blocker_count=0,
        warning_count=0,
    )

    assert estimate.complexity_band == expected_band
