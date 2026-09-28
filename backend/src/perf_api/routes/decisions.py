"""HTTP boundary for workload decisions."""

from fastapi import APIRouter, HTTPException, status

from perf_api.decision import evaluate_workload
from perf_api.decision_schemas import WorkloadDecision, WorkloadDecisionRequest

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.post("/evaluate", response_model=WorkloadDecision)
def evaluate_decision(request: WorkloadDecisionRequest) -> WorkloadDecision:
    """Evaluate an already-normalized workbook against explicit workload targets."""
    try:
        return evaluate_workload(request.workbook, request.targets, request.assumptions)
    except NotImplementedError as err:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(err)) from err
