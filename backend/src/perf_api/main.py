"""Application entry point."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from perf_api.routes.comparisons import router as comparisons_router
from perf_api.routes.decisions import router as decisions_router
from perf_api.routes.workbooks import router as workbooks_router


class HealthResponse(BaseModel):
    """Public response returned by the health endpoint."""

    status: Literal["ok"]
    service: str


app = FastAPI(
    title="Performance Workbook API",
    description="Normalize uploaded performance projections and evaluate workload targets.",
    version="0.1.0",
)

app.include_router(workbooks_router)
app.include_router(decisions_router)
app.include_router(comparisons_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Report that the HTTP application started successfully."""
    return HealthResponse(status="ok", service="perf-api")
