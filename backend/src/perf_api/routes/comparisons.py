"""Multi-workbook upload entry point for issue #6."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from perf_api.comparison import compare_workbooks
from perf_api.comparison_schemas import ComparisonDiagnostic, ComparisonResponse
from perf_api.parser import WorkbookParseError, parse_and_normalize_workbook
from perf_api.schemas import WorkbookNormalizationResponse

router = APIRouter(prefix="/api/v1/comparisons", tags=["comparisons"])


@router.post("/workbooks", response_model=ComparisonResponse)
async def compare_uploaded_workbooks(
    workbooks: Annotated[
        list[UploadFile],
        File(description="One or more .xlsx performance projection workbooks."),
    ],
) -> ComparisonResponse:
    """Normalize every upload through the existing parser, then align them."""
    if not workbooks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one workbook file must be provided.",
        )

    parsed_workbooks: list[WorkbookNormalizationResponse] = []
    diagnostics: list[ComparisonDiagnostic] = []

    for upload in workbooks:
        filename = upload.filename or ""
        if not filename.lower().endswith(".xlsx"):
            diagnostics.append(
                ComparisonDiagnostic(
                    code="INVALID_FILE_TYPE",
                    message=f"File '{filename or '<unnamed>'}' must have a .xlsx filename.",
                    filename=filename or None,
                )
            )
            continue

        content = await upload.read()
        try:
            wb_resp = parse_and_normalize_workbook(content, filename)
            parsed_workbooks.append(wb_resp)
        except WorkbookParseError as err:
            diagnostics.append(
                ComparisonDiagnostic(
                    code="PARSER_ERROR",
                    message=str(err),
                    filename=filename,
                )
            )

    result = compare_workbooks(parsed_workbooks, initial_diagnostics=diagnostics)
    if not result.workbooks or not result.configurations:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[item.model_dump() for item in result.diagnostics],
        )
    return result
