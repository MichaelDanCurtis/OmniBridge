from omnibridge_agent_tools.models import AnalysisResult
from pydantic import BaseModel, ConfigDict


class AgentUsageRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: str
    agent_name: str
    trace_id: str
    estimated_tokens: int
    actual_input_tokens: int
    actual_output_tokens: int
    rate_per_1k_tokens_usd: float

    @property
    def actual_tokens(self) -> int:
        return self.actual_input_tokens + self.actual_output_tokens


class AgentUsageCharge(BaseModel):
    model_config = ConfigDict(frozen=True)

    project_id: str
    agent_name: str
    trace_id: str
    estimated_tokens: int
    actual_tokens: int
    token_variance: int
    estimated_charge_usd: float
    actual_charge_usd: float


def _charge_usd(tokens: int, rate_per_1k_tokens_usd: float) -> float:
    return round((tokens / 1000) * rate_per_1k_tokens_usd, 2)


def reconcile_agent_usage(usage: AgentUsageRecord) -> AgentUsageCharge:
    return AgentUsageCharge(
        project_id=usage.project_id,
        agent_name=usage.agent_name,
        trace_id=usage.trace_id,
        estimated_tokens=usage.estimated_tokens,
        actual_tokens=usage.actual_tokens,
        token_variance=usage.actual_tokens - usage.estimated_tokens,
        estimated_charge_usd=_charge_usd(
            usage.estimated_tokens,
            usage.rate_per_1k_tokens_usd,
        ),
        actual_charge_usd=_charge_usd(
            usage.actual_tokens,
            usage.rate_per_1k_tokens_usd,
        ),
    )


def build_trace_metadata(
    project_id: str,
    agent_name: str,
    result: AnalysisResult,
    usage: AgentUsageRecord | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "project_id": project_id,
        "agent_name": agent_name,
        "requires_consultant_review": result.requires_consultant_review,
        "decision_point_count": len(result.decision_points),
    }
    if usage is None:
        return metadata

    charge = reconcile_agent_usage(usage)
    metadata.update(
        {
            "langfuse_trace_id": usage.trace_id,
            "estimated_agent_tokens": charge.estimated_tokens,
            "actual_agent_tokens": charge.actual_tokens,
            "token_variance": charge.token_variance,
            "estimated_agent_usage_charge_usd": charge.estimated_charge_usd,
            "actual_agent_usage_charge_usd": charge.actual_charge_usd,
        }
    )
    return metadata
