from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ValidationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ValidationCheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    check_id: str
    target_name: str
    status: ValidationStatus
    evidence: str
    remediation: str | None = None


class ValidationSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_checks: int
    pending: int
    passed: int
    failed: int
    blocked: int


class ValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: str
    wave_id: str
    summary: ValidationSummary
    checks: tuple[ValidationCheckResult, ...]
