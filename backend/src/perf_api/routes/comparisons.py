"""Multi-workbook upload entry point for issue #6."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from perf_api.comparison_schemas import ComparisonResponse

router = APIRouter(prefix="/api/v1/comparisons", tags=["comparisons"])


@router.post("/workbooks", response_model=ComparisonResponse)
async def compare_uploaded_workbooks(
    workbooks: Annotated[
        list[UploadFile],
        File(description="One or more .xlsx performance projection workbooks."),
    ],
) -> ComparisonResponse:
    """Normalize every upload through the existing parser, then align them.

    TODO(issue #6, step 5): Validate upload count and each filename; read each
    file; call parse_and_normalize_workbook for every file, including a single
    upload; call compare_workbooks once. Define the error response for invalid
    files and include the filename in each actionable diagnostic.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Issue #6 multi-workbook comparison is not implemented yet.",
    )
