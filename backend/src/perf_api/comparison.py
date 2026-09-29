"""Pure comparison logic for issue #6; no HTTP or workbook byte handling here."""

from collections.abc import Sequence

from perf_api.comparison_schemas import ComparisonResponse
from perf_api.schemas import WorkbookNormalizationResponse


def compare_workbooks(workbooks: Sequence[WorkbookNormalizationResponse]) -> ComparisonResponse:
    """Align normalized sweeps, independent of upload order.

    TODO(issue #6, step 2): Reject duplicate model/profile sweeps and duplicate
    configuration keys within a sweep with useful diagnostics.
    TODO(issue #6, step 3): Build canonical keys from profile, scenario, and
    batch; group rows by key; report missing models and comparability.
    TODO(issue #6, step 4): Sort models, keys, members, and diagnostics so
    reversing upload order produces the same response.
    """
    raise NotImplementedError("Issue #6 comparison logic is learner-owned and not implemented")
