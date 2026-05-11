from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from omnibridge_api.intake_state import get_release1_intake_snapshot
from omnibridge_api.release1_demo import build_release1_demo


router = APIRouter(prefix="/remediation-plans", tags=["remediation-plans"])


class RemediationPlanRequest(BaseModel):
    compute_nodes: list[str] = Field(min_length=1)


class RemediationTask(BaseModel):
    task_id: str
    target_name: str
    rule_id: str
    severity: str
    owner_role: str
    automation_mode: str
    approval_required: bool
    recommended_action: str


class RemediationPlanResponse(BaseModel):
    plan_id: str
    status: str
    task_count: int
    tasks: list[RemediationTask]
    next_action: str


@router.post("/release1-demo")
def create_release1_demo_remediation_plan(
    request: RemediationPlanRequest,
) -> dict[str, object]:
    intake = get_release1_intake_snapshot()
    if not intake.discovery.estimate_ready:
        raise HTTPException(
            status_code=409,
            detail="Discovery must complete before remediation planning can run.",
        )

    demo = build_release1_demo()
    workspace = demo.workspace
    vms_by_name = {vm["name"]: vm for vm in workspace["inventory"]["vms"]}
    unknown_compute_nodes = [
        name for name in request.compute_nodes
        if name not in vms_by_name
    ]
    if unknown_compute_nodes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown compute nodes: {', '.join(unknown_compute_nodes)}",
        )

    tasks = _release1_remediation_tasks(request.compute_nodes, workspace)
    response = RemediationPlanResponse(
        plan_id="remediation-wave-001",
        status="consultant_review_required" if tasks else "no_action_required",
        task_count=len(tasks),
        tasks=tasks,
        next_action=(
            "Assign remediation tasks before test migration."
            if tasks
            else "Continue to test migration approval."
        ),
    )
    return response.model_dump(mode="json")


def _release1_remediation_tasks(
    selected_compute_nodes: list[str],
    workspace: dict[str, Any],
) -> list[RemediationTask]:
    tasks = []
    for finding in workspace["readiness"]["findings"]:
        if finding["target_name"] not in selected_compute_nodes:
            continue
        tasks.append(
            RemediationTask(
                task_id=_task_id(str(finding["target_name"]), str(finding["rule_id"])),
                target_name=finding["target_name"],
                rule_id=finding["rule_id"],
                severity=finding["severity"],
                owner_role=_owner_role(str(finding["rule_id"])),
                automation_mode="human_approved_manual_step",
                approval_required=finding["severity"] == "blocker",
                recommended_action=_recommended_action(str(finding["rule_id"])),
            )
        )

    return tasks


def _task_id(target_name: str, rule_id: str) -> str:
    normalized_rule = rule_id.replace(".", "-")
    return f"remediate-{target_name}-{normalized_rule}"


def _owner_role(rule_id: str) -> str:
    if rule_id.startswith("vmware."):
        return "VMware administrator"
    return "Migration consultant"


def _recommended_action(rule_id: str) -> str:
    actions = {
        "vmware.snapshot.exists": "Consolidate or remove VMware snapshots before replication.",
        "vmware.tools.outdated": (
            "Repair or update VMware Tools before relying on guest metadata."
        ),
    }
    return actions.get(rule_id, "Review the readiness finding and document a remediation path.")
