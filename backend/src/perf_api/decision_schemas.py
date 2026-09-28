"""Inputs and outputs for a customer workload decision."""

from typing import Literal

from pydantic import BaseModel, Field

from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse

MetricName = Literal["throughput", "generation_speed", "ttft", "context", "cost"]
DecisionStatus = Literal["go", "no_go", "insufficient_data"]
EvidenceOutcome = Literal["met", "unmet", "unknown"]


class WorkloadTargets(BaseModel):
    """Customer request: scenario first, then optional acceptance thresholds.

    input_tokens, output_tokens, and cache_fraction identify the workload shape
    represented by a projected row. The remaining fields are constraints to
    check. None means the caller did not supply that fact or limit; it must not
    be replaced with an invented default. Token rates are tokens/second, TTFT
    is milliseconds, and the cost ceiling is USD per million tokens.

    """

    input_tokens: int | None = Field(default=None, gt=0)
    output_tokens: int | None = Field(default=None, gt=0)
    cache_fraction: float | None = Field(default=None, ge=0, le=1)
    min_throughput_tps: float | None = Field(default=None, gt=0)
    min_generation_speed_tps_per_user: float | None = Field(default=None, gt=0)
    max_ttft_ms: float | None = Field(default=None, gt=0)
    min_context_window_tokens: int | None = Field(default=None, gt=0)
    max_cost_usd_per_million_tokens: float | None = Field(default=None, gt=0)


class DecisionAssumptions(BaseModel):
    """Caller-supplied facts that the workbook does not establish.

    context_window_tokens is the supported model/service limit, not the input
    length of a projected scenario. hardware_cost_usd_per_box_hour is an input
    to a capacity-based cost estimate, not a published customer price. Record
    supplied values and their limitations in the decision response.
    """

    context_window_tokens: int | None = Field(default=None, gt=0)
    hardware_cost_usd_per_box_hour: float | None = Field(default=None, ge=0)


class WorkloadDecisionRequest(BaseModel):
    """Normalized workbook and explicit inputs sent to the decision endpoint."""

    workbook: WorkbookNormalizationResponse
    targets: WorkloadTargets
    assumptions: DecisionAssumptions


class ConstraintEvidence(BaseModel):
    """One requested check, including its inputs and its result.

    For met/unmet, actual and target make the comparison reproducible. For
    unknown, leave unavailable values as None and explain which fact is absent.
    Use the same unit for actual and target. The metric identifies which of the
    five supported constraints the evidence describes.
    """

    metric: MetricName
    outcome: EvidenceOutcome
    actual: float | None
    target: float | None
    unit: str
    explanation: str


class ConfigurationEvaluation(BaseModel):
    """Constraint results for one complete projected configuration."""

    record: PerformanceRecord
    evidence: list[ConstraintEvidence]
    unmet_constraints: list[MetricName]
    unknown_constraints: list[MetricName]


class WorkloadDecision(BaseModel):
    """Verdict and supporting evidence for one normalized projection sweep.

    selected_record and top-level evidence describe the representative row.
    evaluated_configurations show why other matching rows did or did not pass.
    unmet_constraints names checked failures; unknown_constraints names checks
    blocked by missing facts. A go is conditional on projections and listed
    assumptions, not a production performance guarantee.
    """

    status: DecisionStatus
    model_name: str
    profile_id: str
    selected_record: PerformanceRecord | None
    selection_explanation: str
    evidence: list[ConstraintEvidence]
    evaluated_configurations: list[ConfigurationEvaluation]
    unmet_constraints: list[MetricName]
    unknown_constraints: list[MetricName]
    assumptions: list[str]
