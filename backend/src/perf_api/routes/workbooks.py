from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from perf_api.parser import WorkbookParseError, parse_and_normalize_workbook
from perf_api.schemas import WorkbookNormalizationResponse

router = APIRouter(prefix="/api/v1/workbooks", tags=["workbooks"])


@router.post("/normalize", response_model=WorkbookNormalizationResponse)
async def normalize_workbook(
    workbook: Annotated[
        UploadFile,
        File(description="One performance projection workbook in .xlsx format."),
    ],
) -> WorkbookNormalizationResponse:
    """Validate and normalize one uploaded performance workbook."""

    if not workbook.filename or not workbook.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx workbook files are supported.",
        )

    contents = await workbook.read()

    try:
        return parse_and_normalize_workbook(file_bytes=contents, filename=workbook.filename)
    except WorkbookParseError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)
        ) from err
