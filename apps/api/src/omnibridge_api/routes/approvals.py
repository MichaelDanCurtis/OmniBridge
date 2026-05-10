from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from omnibridge_workflow_engine.models import (
    ApprovalLedger,
    ApprovalRecord,
    ProjectWorkflowSnapshot,
    WorkflowState,
)


router = APIRouter(prefix="/approvals", tags=["approvals"])
_release1_ledger = ApprovalLedger.seed_release1()


class ApprovalRequest(BaseModel):
    actor: str
    reason: str


def _release1_snapshot() -> ProjectWorkflowSnapshot:
    return ProjectWorkflowSnapshot(
        state=WorkflowState.BLUEPRINT_GENERATED,
        approvals=_release1_ledger.records,
    )


@router.get("/release1-demo")
def release1_demo_approvals() -> dict[str, object]:
    return _release1_snapshot().model_dump(mode="json")


@router.post("/release1-demo/{gate}/approve")
def approve_release1_gate(
    gate: str,
    request: ApprovalRequest,
) -> dict[str, object]:
    try:
        record: ApprovalRecord = _release1_ledger.approve(
            gate=gate,
            actor=request.actor,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return record.model_dump(mode="json")
