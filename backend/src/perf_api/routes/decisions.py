"""HTTP boundary for workload decisions."""

from fastapi import APIRouter

from perf_api.decision import evaluate_workload
from perf_api.decision_schemas import WorkloadDecision, WorkloadDecisionRequest

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.post("/evaluate", response_model=WorkloadDecision)
def evaluate_decision(request: WorkloadDecisionRequest) -> WorkloadDecision:
    """Validate the JSON contract and delegate all decision rules to the domain function.

    Send the normalization endpoint's response as workbook, plus targets and
    assumptions. FastAPI/Pydantic reject malformed inputs before this function
    runs.
    """
    return evaluate_workload(request.workbook, request.targets, request.assumptions)
