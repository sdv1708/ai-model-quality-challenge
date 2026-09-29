"""HTTP boundary for the learner-owned engineering analysis endpoint."""

from fastapi import APIRouter, HTTPException, status

from perf_api.engineering_schemas import EngineeringAnalysisRequest, EngineeringAnalysisResponse

router = APIRouter(prefix="/api/v1/engineering", tags=["engineering"])


@router.post("/analyze", response_model=EngineeringAnalysisResponse)
def analyze_engineering_request(
    request: EngineeringAnalysisRequest,
) -> EngineeringAnalysisResponse:
    """Expose the issue #8 contract while its analysis is still a TODO."""
    # TODO(8.6): Call the pure analysis function once TODOs 8.1-8.5 are complete.
    # Keep request validation and HTTP error handling here, outside the domain logic.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Engineering analysis for issue #8 is not implemented yet.",
    )
