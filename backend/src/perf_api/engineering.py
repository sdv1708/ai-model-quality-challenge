"""Learner-owned analysis seam for issue #8; no HTTP or workbook parsing here."""

from perf_api.engineering_schemas import EngineeringAnalysisResponse
from perf_api.schemas import WorkbookNormalizationResponse


def analyze_engineering(
    workbooks: list[WorkbookNormalizationResponse],
) -> EngineeringAnalysisResponse:
    """Turn normalized projections into engineering evidence.

    TODO(8.1): Choose comparable configuration keys and stable output ordering.
    TODO(8.2): Preserve every source record and report raw metrics with units.
    TODO(8.3): Derive cache, aggregate/per-box, batch, and scaling observations.
    TODO(8.4): Add deterministic, explainable anomaly rules without rejecting rows.
    TODO(8.5): State projection and comparison limitations in the response.
    """
    raise NotImplementedError("Issue #8 engineering analysis is learner-owned and pending")
