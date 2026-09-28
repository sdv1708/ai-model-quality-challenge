"""Behavior cases for workload decisions.

TODO(issue #4): Remove one skip marker at a time, implement its behavior in
decision.py, then add cases just above/below each threshold and for mixed
failed/unknown constraints. Assert evidence values and units, not only status.
"""

from pathlib import Path
from zipfile import ZipFile

import pytest

from perf_api.decision import evaluate_workload
from perf_api.decision_schemas import DecisionAssumptions, WorkloadTargets
from perf_api.parser import parse_and_normalize_workbook
from perf_api.schemas import WorkbookNormalizationResponse


@pytest.fixture
def sample_workbook() -> WorkbookNormalizationResponse:
    """Use the same projection that the upload endpoint accepts."""
    zip_path = Path(__file__).parents[2] / "perf_data.zip"
    with ZipFile(zip_path) as archive:
        workbook_bytes = archive.read("Model_A_profile_1/Model A profile 1.xlsx")
    return parse_and_normalize_workbook(workbook_bytes, "Model A profile 1.xlsx")


@pytest.mark.skip(reason="TODO(issue #4): Match one row and satisfy all speed thresholds")
def test_one_configuration_meets_all_speed_targets(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """Batch 20 meets the three limits together; faster aggregate rows do not."""
    targets = WorkloadTargets(
        input_tokens=10_000,
        output_tokens=333,
        cache_fraction=0.5,
        min_throughput_tps=400_000,
        min_generation_speed_tps_per_user=1_200,
        max_ttft_ms=10,
    )

    result = evaluate_workload(sample_workbook, targets, DecisionAssumptions())

    assert result.status == "go"
    assert result.selected_record is not None
    assert result.selected_record.batch_size == 20
    assert not result.unmet_constraints
    assert not result.unknown_constraints


@pytest.mark.skip(reason="TODO(issue #4): Do not combine metrics from different rows")
def test_metrics_from_different_rows_cannot_be_combined(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """High throughput and high per-user speed exist, but never on one row."""
    targets = WorkloadTargets(
        min_throughput_tps=550_000,
        min_generation_speed_tps_per_user=1_300,
    )

    result = evaluate_workload(sample_workbook, targets, DecisionAssumptions())

    assert result.status == "no_go"
    assert result.unmet_constraints


@pytest.mark.skip(reason="TODO(issue #4): Keep missing targets explicit")
def test_missing_targets_do_not_produce_a_go(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A decision without customer limits must not claim the workload fits."""
    result = evaluate_workload(sample_workbook, WorkloadTargets(), DecisionAssumptions())

    assert result.status == "insufficient_data"


@pytest.mark.skip(reason="TODO(issue #4): Mark absent context and price as unknown")
def test_missing_context_and_price_remain_unknown(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """Workbook scenarios contain neither supported context nor hardware price."""
    targets = WorkloadTargets(
        min_context_window_tokens=12_000,
        max_cost_usd_per_million_tokens=1,
    )

    result = evaluate_workload(sample_workbook, targets, DecisionAssumptions())

    assert result.status == "insufficient_data"
    assert set(result.unknown_constraints) == {"context", "cost"}


@pytest.mark.skip(reason="TODO(issue #4): Make threshold comparisons inclusive")
def test_equal_values_meet_inclusive_thresholds(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """Values exactly on minimum and maximum limits count as met."""
    first = sample_workbook.records[0]
    targets = WorkloadTargets(
        min_throughput_tps=first.throughput,
        min_generation_speed_tps_per_user=first.gen_speed,
        max_ttft_ms=first.ttft_ms,
    )

    result = evaluate_workload(sample_workbook, targets, DecisionAssumptions())

    assert result.status == "go"
    assert result.selected_record is not None
    assert result.selected_record.batch_size == first.batch_size
