from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from omnibridge_api.intake_state import get_release1_intake_snapshot
from omnibridge_api.release1_demo import build_release1_demo
from omnibridge_api.routes.approvals import is_release1_gate_approved


router = APIRouter(prefix="/migration-waves", tags=["migration-waves"])


class MigrationWaveRequest(BaseModel):
    compute_nodes: list[str] = Field(min_length=1)


class MigrationWaveBlocker(BaseModel):
    name: str
    readiness: str
    message: str


class MigrationWaveResponse(BaseModel):
    wave_id: str
    status: str
    selected_compute_nodes: list[str]
    execution_backend: str
    operation_count: int
    approval_gates: list[str]
    ready_count: int
    blocked_count: int
    blockers: list[MigrationWaveBlocker]
    next_action: str


@router.post("/release1-demo")
def create_release1_demo_migration_wave(
    request: MigrationWaveRequest,
) -> dict[str, object]:
    intake = get_release1_intake_snapshot()
    if not intake.discovery.estimate_ready:
        raise HTTPException(
            status_code=409,
            detail="Discovery must complete before a migration wave can be created.",
        )

    if not is_release1_gate_approved("commercial_estimate_approval"):
        raise HTTPException(
            status_code=409,
            detail="Commercial estimate must be approved before creating a migration wave.",
        )

    demo = build_release1_demo()
    vms_by_name = {vm["name"]: vm for vm in demo.workspace["inventory"]["vms"]}
    unknown_compute_nodes = [
        name for name in request.compute_nodes
        if name not in vms_by_name
    ]
    if unknown_compute_nodes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown compute nodes: {', '.join(unknown_compute_nodes)}",
        )

    blockers = _release1_wave_blockers(request.compute_nodes, demo.workspace)
    selected_vm_count = len(request.compute_nodes)
    response = MigrationWaveResponse(
        wave_id="wave-001",
        status="ready_for_test_migration",
        selected_compute_nodes=request.compute_nodes,
        execution_backend="azure-migrate",
        operation_count=selected_vm_count + 4,
        approval_gates=[
            "test_migration_approval",
            "source_shutdown_approval",
            "cutover_approval",
        ],
        ready_count=selected_vm_count - len(blockers),
        blocked_count=len(blockers),
        blockers=blockers,
        next_action=(
            "Resolve blockers before test migration."
            if blockers
            else "Request test migration approval."
        ),
    )

    return response.model_dump(mode="json")


def _release1_wave_blockers(
    selected_compute_nodes: list[str],
    workspace: dict[str, object],
) -> list[MigrationWaveBlocker]:
    findings = workspace["readiness"]["findings"]  # type: ignore[index]
    blockers = []
    for finding in findings:
        if finding["severity"] != "blocker":
            continue
        if finding["target_name"] not in selected_compute_nodes:
            continue
        blockers.append(
            MigrationWaveBlocker(
                name=finding["target_name"],
                readiness="Blocked",
                message=finding["message"],
            )
        )

    return blockers
