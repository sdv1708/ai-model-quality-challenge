"""HTTP boundary for workload decisions."""

from fastapi import APIRouter, HTTPException, status

from perf_api.decision import evaluate_workload
from perf_api.decision_schemas import WorkloadDecision, WorkloadDecisionRequest

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.post("/evaluate", response_model=WorkloadDecision)
def evaluate_decision(request: WorkloadDecisionRequest) -> WorkloadDecision:
    """Validate the JSON contract and delegate all decision rules to the domain function.

    Send the normalization endpoint's response as workbook, plus targets and
    assumptions. FastAPI/Pydantic reject malformed inputs before this function
    runs. The temporary 501 response makes the unimplemented evaluator explicit.
    """
    # TODO(issue #4): Remove the temporary 501 mapping after the evaluator works.
    try:
        return evaluate_workload(request.workbook, request.targets, request.assumptions)
    except NotImplementedError as err:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(err)) from err
