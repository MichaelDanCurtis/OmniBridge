from collections import Counter
from collections.abc import Sequence

from omnibridge_validation_engine.models import (
    ValidationCheckResult,
    ValidationEvidence,
    ValidationStatus,
    ValidationSummary,
)

_STANDARD_CHECKS = (
    "vm_boot",
    "azure_agent",
    "disk_attachment",
    "nic_addressing",
    "service_ports",
    "tcp_1433",
)


def build_release1_validation_evidence(
    *,
    project_id: str,
    wave_id: str,
    compute_node_names: Sequence[str],
    blocked_compute_nodes: Sequence[str] = (),
) -> ValidationEvidence:
    blocked_names = set(blocked_compute_nodes)
    checks = tuple(
        ValidationCheckResult(
            check_id=check_id,
            target_name=compute_node_name,
            status=(
                ValidationStatus.BLOCKED
                if compute_node_name in blocked_names
                else ValidationStatus.PENDING
            ),
            evidence="Awaiting test migration execution.",
            remediation=(
                "Resolve preflight blockers before test migration."
                if compute_node_name in blocked_names
                else None
            ),
        )
        for compute_node_name in compute_node_names
        for check_id in _STANDARD_CHECKS
    )
    counts = Counter(check.status for check in checks)

    return ValidationEvidence(
        project_id=project_id,
        wave_id=wave_id,
        summary=ValidationSummary(
            total_checks=len(checks),
            pending=counts[ValidationStatus.PENDING],
            passed=counts[ValidationStatus.PASSED],
            failed=counts[ValidationStatus.FAILED],
            blocked=counts[ValidationStatus.BLOCKED],
        ),
        checks=checks,
    )
