from omnibridge_validation_engine.models import ValidationStatus
from omnibridge_validation_engine.vmware_to_azure import build_release1_validation_evidence


def test_release1_validation_evidence_marks_checks_pending_before_test_migration() -> None:
    evidence = build_release1_validation_evidence(
        project_id="project-release1-vmware-azure",
        wave_id="wave-001",
        compute_node_names=("claims-web-01", "claims-api-01", "claims-db-01"),
    )

    assert evidence.project_id == "project-release1-vmware-azure"
    assert evidence.wave_id == "wave-001"
    assert evidence.summary.total_checks == 18
    assert evidence.summary.pending == 18
    assert evidence.summary.failed == 0
    assert evidence.checks[0].check_id == "vm_boot"
    assert evidence.checks[0].target_name == "claims-web-01"
    assert evidence.checks[0].status == ValidationStatus.PENDING
    assert evidence.checks[-1].check_id == "tcp_1433"
    assert evidence.checks[-1].target_name == "claims-db-01"


def test_release1_validation_evidence_can_mark_blocked_checks() -> None:
    evidence = build_release1_validation_evidence(
        project_id="project-release1-vmware-azure",
        wave_id="wave-001",
        compute_node_names=("claims-web-01", "claims-db-01"),
        blocked_compute_nodes=("claims-db-01",),
    )

    blocked = [check for check in evidence.checks if check.status == ValidationStatus.BLOCKED]

    assert evidence.summary.blocked == 6
    assert {check.target_name for check in blocked} == {"claims-db-01"}
    assert blocked[0].remediation == "Resolve preflight blockers before test migration."
