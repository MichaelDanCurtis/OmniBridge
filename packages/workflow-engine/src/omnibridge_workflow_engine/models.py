from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class WorkflowState(StrEnum):
    DISCOVERED = "DISCOVERED"
    GRAPH_INGESTED = "GRAPH_INGESTED"
    ANALYZED = "ANALYZED"
    ESTIMATED = "ESTIMATED"
    BLUEPRINT_GENERATED = "BLUEPRINT_GENERATED"


class ApprovalRecord(BaseModel):
    gate: str
    status: str = "pending"
    actor: str | None = None
    reason: str | None = None


class ApprovalLedger(BaseModel):
    records: list[ApprovalRecord] = Field(default_factory=list)

    @classmethod
    def seed_release1(cls) -> "ApprovalLedger":
        return cls(
            records=[
                ApprovalRecord(gate="commercial_estimate_approval"),
                ApprovalRecord(gate="target_design_approval"),
                ApprovalRecord(gate="blueprint_approval"),
                ApprovalRecord(gate="test_migration_approval"),
                ApprovalRecord(gate="source_shutdown_approval"),
                ApprovalRecord(gate="cutover_approval"),
            ]
        )

    @property
    def pending_gates(self) -> list[str]:
        return [
            record.gate
            for record in self.records
            if record.status == "pending"
        ]

    def approve(self, gate: str, actor: str, reason: str) -> ApprovalRecord:
        for index, record in enumerate(self.records):
            if record.gate != gate:
                continue

            approved = record.model_copy(
                update={
                    "actor": actor,
                    "reason": reason,
                    "status": "approved",
                }
            )
            self.records[index] = approved
            return approved

        raise ValueError(f"Unknown approval gate: {gate}")


class ProjectWorkflowSnapshot(BaseModel):
    state: WorkflowState
    approvals: list[ApprovalRecord]

    @computed_field
    @property
    def pending_approval_count(self) -> int:
        return sum(record.status == "pending" for record in self.approvals)


def derive_workflow_state(
    *,
    graph_ingested: bool,
    analyzed: bool = False,
    estimated: bool = False,
    blueprint_generated: bool = False,
) -> WorkflowState:
    if blueprint_generated:
        return WorkflowState.BLUEPRINT_GENERATED
    if estimated:
        return WorkflowState.ESTIMATED
    if analyzed:
        return WorkflowState.ANALYZED
    if graph_ingested:
        return WorkflowState.GRAPH_INGESTED
    return WorkflowState.DISCOVERED
