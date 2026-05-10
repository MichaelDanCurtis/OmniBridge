import pytest

from omnibridge_workflow_engine.models import (
    ApprovalLedger,
    ProjectWorkflowSnapshot,
    WorkflowState,
    derive_workflow_state,
)


def test_derive_workflow_state_advances_through_release1_states() -> None:
    assert derive_workflow_state(graph_ingested=False) == WorkflowState.DISCOVERED
    assert derive_workflow_state(graph_ingested=True) == WorkflowState.GRAPH_INGESTED
    assert (
        derive_workflow_state(graph_ingested=True, analyzed=True)
        == WorkflowState.ANALYZED
    )
    assert (
        derive_workflow_state(graph_ingested=True, analyzed=True, estimated=True)
        == WorkflowState.ESTIMATED
    )
    assert (
        derive_workflow_state(
            graph_ingested=True,
            analyzed=True,
            estimated=True,
            blueprint_generated=True,
        )
        == WorkflowState.BLUEPRINT_GENERATED
    )


def test_approval_ledger_records_known_gate_approvals() -> None:
    ledger = ApprovalLedger.seed_release1()

    record = ledger.approve(
        gate="commercial_estimate_approval",
        actor="consultant@example.com",
        reason="Customer accepted assessment package.",
    )

    assert record.gate == "commercial_estimate_approval"
    assert record.status == "approved"
    assert record.actor == "consultant@example.com"
    assert ledger.pending_gates == [
        "target_design_approval",
        "blueprint_approval",
        "test_migration_approval",
        "source_shutdown_approval",
        "cutover_approval",
    ]


def test_approval_ledger_rejects_unknown_gate() -> None:
    ledger = ApprovalLedger.seed_release1()

    with pytest.raises(ValueError, match="Unknown approval gate"):
        ledger.approve(
            gate="delete_source_vm",
            actor="consultant@example.com",
            reason="Unsafe operation.",
        )


def test_workflow_snapshot_combines_state_and_approvals() -> None:
    ledger = ApprovalLedger.seed_release1()
    snapshot = ProjectWorkflowSnapshot(
        state=WorkflowState.BLUEPRINT_GENERATED,
        approvals=ledger.records,
    )

    assert snapshot.state == WorkflowState.BLUEPRINT_GENERATED
    assert snapshot.pending_approval_count == 6
