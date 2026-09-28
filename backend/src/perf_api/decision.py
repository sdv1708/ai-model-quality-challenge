"""Decision rules for projected workbook performance (issue #4)."""

from perf_api.decision_schemas import DecisionAssumptions, WorkloadDecision, WorkloadTargets
from perf_api.schemas import WorkbookNormalizationResponse


def evaluate_workload(
    workbook: WorkbookNormalizationResponse,
    targets: WorkloadTargets,
    assumptions: DecisionAssumptions,
) -> WorkloadDecision:
    """Evaluate complete workbook rows against explicit workload requirements."""
    raise NotImplementedError("Implement issue #4 workload decision rules")
