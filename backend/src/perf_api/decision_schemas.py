"""Inputs and outputs for a customer workload decision."""

from typing import Literal

from pydantic import BaseModel, Field

from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse

MetricName = Literal["throughput", "generation_speed", "ttft", "context", "cost"]
DecisionStatus = Literal["go", "no_go", "insufficient_data"]
EvidenceOutcome = Literal["met", "unmet", "unknown"]


class WorkloadTargets(BaseModel):
    """Customer-supplied workload shape and optional decision thresholds."""

    input_tokens: int | None = Field(default=None, gt=0)
    output_tokens: int | None = Field(default=None, gt=0)
    cache_fraction: float | None = Field(default=None, ge=0, le=1)
    min_throughput_tps: float | None = Field(default=None, gt=0)
    min_generation_speed_tps_per_user: float | None = Field(default=None, gt=0)
    max_ttft_ms: float | None = Field(default=None, gt=0)
    min_context_window_tokens: int | None = Field(default=None, gt=0)
    max_cost_usd_per_million_tokens: float | None = Field(default=None, gt=0)


class DecisionAssumptions(BaseModel):
    """Facts unavailable in the workbook that a caller may explicitly supply."""

    context_window_tokens: int | None = Field(default=None, gt=0)
    hardware_cost_usd_per_box_hour: float | None = Field(default=None, ge=0)


class WorkloadDecisionRequest(BaseModel):
    """Normalized workbook and explicit inputs sent to the decision endpoint."""

    workbook: WorkbookNormalizationResponse
    targets: WorkloadTargets
    assumptions: DecisionAssumptions


class ConstraintEvidence(BaseModel):
    """A threshold comparison or an explanation of why it cannot be made."""

    metric: MetricName
    outcome: EvidenceOutcome
    actual: float | None
    target: float | None
    unit: str
    explanation: str


class WorkloadDecision(BaseModel):
    """Explainable result for one workbook and one set of workload targets."""

    status: DecisionStatus
    model_name: str
    profile_id: str
    selected_record: PerformanceRecord | None
    evidence: list[ConstraintEvidence]
    unmet_constraints: list[MetricName]
    unknown_constraints: list[MetricName]
    assumptions: list[str]
