"""Behavior cases for projected workload decisions."""

import math
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
    assert len(result.evaluated_configurations) == len(sample_workbook.records)
    assert all(row.unmet_constraints for row in result.evaluated_configurations)
    assert "every matching configuration" in result.selection_explanation.lower()


def test_missing_targets_do_not_produce_a_go(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A decision without customer limits must not claim the workload fits."""
    result = evaluate_workload(sample_workbook, WorkloadTargets(), DecisionAssumptions())

    assert result.status == "insufficient_data"
    assert result.selected_record is None
    assert "No decision thresholds" in result.selection_explanation


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


def test_context_window_must_cover_the_projected_scenario(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A claimed 8k window cannot serve the 10k-input/333-output sample row."""
    targets = WorkloadTargets(
        input_tokens=10_000,
        output_tokens=333,
        min_throughput_tps=400_000,
        min_context_window_tokens=8_000,
    )

    result = evaluate_workload(
        sample_workbook, targets, DecisionAssumptions(context_window_tokens=8_000)
    )

    assert result.status == "no_go"
    context = next(item for item in result.evidence if item.metric == "context")
    assert context.outcome == "unmet"
    assert context.actual == 8_000
    assert context.target == 10_333
    assert "10333" in context.explanation


def test_context_assumption_cannot_contradict_a_speed_only_decision(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A known context mismatch blocks a go even without a context threshold."""
    result = evaluate_workload(
        sample_workbook,
        WorkloadTargets(min_throughput_tps=400_000),
        DecisionAssumptions(context_window_tokens=8_000),
    )

    assert result.status == "no_go"
    assert "context" in result.unmet_constraints


def test_unmatched_scenario_explains_unknown_targets(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A new input length is unmeasured, not a demonstrated model failure."""
    result = evaluate_workload(
        sample_workbook,
        WorkloadTargets(input_tokens=2_000, min_throughput_tps=400_000, max_ttft_ms=10),
        DecisionAssumptions(),
    )

    assert result.status == "insufficient_data"
    assert result.selected_record is None
    assert not result.evaluated_configurations
    assert "input=2000" in result.selection_explanation
    assert {item.metric for item in result.evidence} == {"throughput", "ttft"}
    assert all(item.outcome == "unknown" and item.actual is None for item in result.evidence)
    assert {(item.target, item.unit) for item in result.evidence} == {(400_000, "t/s"), (10, "ms")}


@pytest.mark.parametrize(
    ("field", "attribute", "unit", "is_minimum"),
    [
        ("min_throughput_tps", "throughput", "t/s", True),
        ("min_generation_speed_tps_per_user", "gen_speed", "t/s/user", True),
        ("max_ttft_ms", "ttft_ms", "ms", False),
    ],
)
def test_limits_just_inside_and_outside_the_boundary(
    sample_workbook: WorkbookNormalizationResponse,
    field: str,
    attribute: str,
    unit: str,
    is_minimum: bool,
) -> None:
    """The sign of each comparison matters immediately either side of equality."""
    first = sample_workbook.records[0]
    single = sample_workbook.model_copy(update={"records": [first], "record_count": 1})
    actual = float(getattr(first, attribute))
    good_limit = actual - 0.01 if is_minimum else actual + 0.01
    bad_limit = actual + 0.01 if is_minimum else actual - 0.01

    good = evaluate_workload(
        single, WorkloadTargets.model_validate({field: good_limit}), DecisionAssumptions()
    )
    bad = evaluate_workload(
        single, WorkloadTargets.model_validate({field: bad_limit}), DecisionAssumptions()
    )

    assert good.status == "go"
    assert bad.status == "no_go"
    assert good.evidence[0].actual == actual
    assert good.evidence[0].target == good_limit
    assert good.evidence[0].unit == unit
    assert bad.evidence[0].outcome == "unmet"


def test_known_failure_and_unknown_context_stay_distinct(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A known throughput failure gives no-go while context remains unknown."""
    first = sample_workbook.records[0]
    single = sample_workbook.model_copy(update={"records": [first], "record_count": 1})
    result = evaluate_workload(
        single,
        WorkloadTargets(
            min_throughput_tps=first.throughput + 1,
            min_context_window_tokens=12_000,
        ),
        DecisionAssumptions(),
    )

    assert result.status == "no_go"
    assert result.unmet_constraints == ["throughput"]
    assert result.unknown_constraints == ["context"]


def test_viable_row_with_unknown_prevents_global_no_go(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """A failing row does not erase another row that could pass with more facts."""
    first_two = sample_workbook.model_copy(
        update={"records": sample_workbook.records[:2], "record_count": 2}
    )
    result = evaluate_workload(
        first_two,
        WorkloadTargets(min_throughput_tps=400_000, min_context_window_tokens=12_000),
        DecisionAssumptions(),
    )

    assert result.status == "insufficient_data"
    assert result.selected_record is not None
    assert result.selected_record.batch_size == 20
    assert result.unknown_constraints == ["context"]
    assert result.evaluated_configurations[0].unmet_constraints == ["throughput"]
    assert result.evaluated_configurations[1].unknown_constraints == ["context"]


def test_cost_uses_supplied_price_and_projected_capacity(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """The cost estimate exposes its numeric basis and full-capacity assumption."""
    first = sample_workbook.records[0]
    single = sample_workbook.model_copy(update={"records": [first], "record_count": 1})
    result = evaluate_workload(
        single,
        WorkloadTargets(max_cost_usd_per_million_tokens=1),
        DecisionAssumptions(hardware_cost_usd_per_box_hour=1),
    )

    assert result.status == "go"
    cost = result.evidence[0]
    assert cost.metric == "cost"
    assert cost.unit == "USD/M projected throughput tokens"
    assert cost.actual is not None
    assert math.isclose(cost.actual, 1_000_000 / (first.throughput_per_box * 3_600))
    assert any("assuming sustained projected capacity" in text for text in result.assumptions)


def test_zero_per_box_throughput_is_a_distinct_cost_unknown(
    sample_workbook: WorkbookNormalizationResponse,
) -> None:
    """An explicit price cannot repair a zero-capacity projection."""
    zero_row = sample_workbook.records[0].model_copy(update={"throughput_per_box": 0})
    single = sample_workbook.model_copy(update={"records": [zero_row], "record_count": 1})
    result = evaluate_workload(
        single,
        WorkloadTargets(max_cost_usd_per_million_tokens=1),
        DecisionAssumptions(hardware_cost_usd_per_box_hour=1),
    )

    assert result.status == "insufficient_data"
    assert result.evidence[0].outcome == "unknown"
    assert "throughput_per_box" in result.evidence[0].explanation
    assert "not supplied" not in result.evidence[0].explanation
