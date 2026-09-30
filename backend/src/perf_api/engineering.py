"""Engineering diagnostics over normalized projection rows, without HTTP concerns."""

import math
from itertools import pairwise
from typing import Literal

from perf_api.engineering_schemas import (
    AnomalyFlag,
    ConfigurationDiagnostic,
    EngineeringAnalysisResponse,
    EngineeringMetric,
    SourceReference,
    TrendDiagnostic,
)
from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse

DECOMPOSITION_REL_TOL = 0.001  # 0.1%; bundled sweeps differ by at most 0.0192%.
DECOMPOSITION_ABS_TOL_TPS = 0.01
SCALING_DROP_FRACTION = 0.05

Row = tuple[SourceReference, PerformanceRecord]
TrendDimension = Literal["batch_size", "cache_percentage"]


def _percent_change(baseline: float, candidate: float) -> str:
    """A percentage is meaningful only with a positive baseline."""
    if baseline <= 0:
        return "percent change unavailable because the baseline is not positive"
    return f"{(candidate - baseline) / baseline * 100:+.2f}%"


def _trend(
    dimension: TrendDimension,
    baseline: Row,
    candidate: Row,
    metric_name: str,
    unit: str,
    label: str,
    baseline_value: float,
    candidate_value: float,
) -> TrendDiagnostic:
    base_source, base_record = baseline
    candidate_source, candidate_record = candidate
    if dimension == "cache_percentage":
        change = (
            f"Cache setting {base_record.cache_percentage * 100:g}% to "
            f"{candidate_record.cache_percentage * 100:g}%"
        )
    else:
        change = f"Batch size {base_record.batch_size} to {candidate_record.batch_size}"

    return TrendDiagnostic(
        dimension=dimension,
        baseline=base_source,
        candidate=candidate_source,
        metric_name=metric_name,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        unit=unit,
        explanation=(
            f"{change}: {label} changed from {baseline_value:g} to "
            f"{candidate_value:g} {unit} ({_percent_change(baseline_value, candidate_value)})."
        ),
    )


def _configuration_metrics(record: PerformanceRecord) -> list[EngineeringMetric]:
    """Keep reported components separate from derived, dimensionless ratios."""
    values = [
        ("throughput", record.throughput, "t/s", "Reported aggregate throughput"),
        (
            "throughput_per_box",
            record.throughput_per_box,
            "t/s/hardware",
            "Reported throughput per hardware box",
        ),
        (
            "cached_throughput",
            record.cached_throughput,
            "t/s",
            "Reported cached throughput component",
        ),
        (
            "uncached_throughput",
            record.uncached_throughput,
            "t/s",
            "Reported uncached throughput component",
        ),
        (
            "cached_throughput_per_box",
            record.cached_throughput_per_box,
            "t/s/hardware",
            "Reported cached throughput per hardware box",
        ),
        (
            "uncached_throughput_per_box",
            record.uncached_throughput_per_box,
            "t/s/hardware",
            "Reported uncached throughput per hardware box",
        ),
        ("ttft_ms", record.ttft_ms, "ms", "Reported time to first token"),
        ("gen_speed", record.gen_speed, "t/s/user", "Reported per-user generation speed"),
        ("rpm", record.rpm, "req/min", "Reported requests per minute"),
    ]
    metrics = [
        EngineeringMetric(name=name, value=value, unit=unit, explanation=explanation)
        for name, value, unit, explanation in values
    ]
    if record.throughput > 0:
        metrics.extend(
            [
                EngineeringMetric(
                    name="cached_share",
                    value=record.cached_throughput / record.throughput,
                    unit="ratio",
                    explanation="Cached throughput component / reported aggregate throughput",
                ),
                EngineeringMetric(
                    name="uncached_share",
                    value=record.uncached_throughput / record.throughput,
                    unit="ratio",
                    explanation="Uncached throughput component / reported aggregate throughput",
                ),
            ]
        )
    if record.throughput_per_box > 0:
        metrics.append(
            EngineeringMetric(
                name="implied_box_capacity_ratio",
                value=record.throughput / record.throughput_per_box,
                unit="ratio",
                explanation=(
                    "Aggregate / per-box throughput; this is not a verified physical box count"
                ),
            )
        )
    return metrics


def _row_anomalies(source: SourceReference, record: PerformanceRecord) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []
    checked = (
        ("throughput", record.throughput, "t/s"),
        ("throughput_per_box", record.throughput_per_box, "t/s/hardware"),
        ("ttft_ms", record.ttft_ms, "ms"),
        ("gen_speed", record.gen_speed, "t/s/user"),
    )
    nonpositive = [f"{name}={value:g} {unit}" for name, value, unit in checked if value <= 0]
    if nonpositive:
        flags.append(
            AnomalyFlag(
                code="ANOMALY_NONPOSITIVE_METRIC",
                rule="Flag reported throughput, TTFT, or generation speed at or below zero",
                explanation=(
                    "Review nonpositive projection value(s): " + ", ".join(nonpositive) + "."
                ),
                sources=[source],
            )
        )

    component_sum = record.cached_throughput + record.uncached_throughput
    if not math.isclose(
        component_sum,
        record.throughput,
        rel_tol=DECOMPOSITION_REL_TOL,
        abs_tol=DECOMPOSITION_ABS_TOL_TPS,
    ):
        delta = abs(component_sum - record.throughput)
        flags.append(
            AnomalyFlag(
                code="ANOMALY_THROUGHPUT_MISMATCH",
                rule=(
                    "Flag when cached + uncached differs from total by more than "
                    "0.1% of the larger magnitude and 0.01 t/s"
                ),
                explanation=(
                    f"Cached {record.cached_throughput:g} + uncached "
                    f"{record.uncached_throughput:g} = {component_sum:g} t/s; "
                    f"reported total is {record.throughput:g} t/s; "
                    f"absolute difference is {delta:g} t/s. The component relationship "
                    "is inferred from the supplied sweeps and warrants review."
                ),
                sources=[source],
            )
        )
    return flags


def _distinct_rows(rows: list[Row], dimension: TrendDimension, limitations: list[str]) -> list[Row]:
    """Use one deterministic row per dimension value; retain every source row elsewhere."""
    ordered = sorted(
        rows,
        key=lambda pair: (getattr(pair[1], dimension), pair[0].record_index),
    )
    distinct: list[Row] = []
    for row in ordered:
        if distinct and getattr(row[1], dimension) == getattr(distinct[-1][1], dimension):
            source = row[0]
            limitations.append(
                f"Repeated {dimension} in model {source.model_name}, profile "
                f"{source.profile_id}, workbook {source.workbook_index}; "
                "one row per value was used for trends. All rows remain in configurations."
            )
            continue
        distinct.append(row)
    return distinct


def analyze_engineering(
    workbooks: list[WorkbookNormalizationResponse],
) -> EngineeringAnalysisResponse:
    """Turn normalized projections into sourced metrics, trends, and review flags."""
    # The serialized tie-breaker makes duplicate model/profile inputs order independent.
    ordered_workbooks = sorted(
        workbooks, key=lambda wb: (wb.model_name, wb.profile_id, wb.model_dump_json())
    )
    configurations: list[ConfigurationDiagnostic] = []
    trends: list[TrendDiagnostic] = []
    anomalies: list[AnomalyFlag] = []
    limitations = [
        "Projections are modeled capacity estimates, not production measurements.",
        "Filename, worksheet, and sheet-row provenance is unavailable in normalized records.",
        "Cached and uncached columns appear to be throughput components; they do not "
        "establish a causal cache speedup.",
        "Percent change is omitted when the baseline is not positive; raw values remain visible.",
    ]
    cache_groups: dict[tuple[int, int, int, int], list[Row]] = {}
    batch_groups: dict[tuple[int, int, int, float], list[Row]] = {}

    for workbook_index, workbook in enumerate(ordered_workbooks):
        for record_index, record in enumerate(workbook.records):
            source = SourceReference(
                model_name=workbook.model_name,
                profile_id=workbook.profile_id,
                workbook_index=workbook_index,
                record_index=record_index,
            )
            row = (source, record)
            configurations.append(
                ConfigurationDiagnostic(
                    source=source,
                    record=record,
                    metrics=_configuration_metrics(record),
                )
            )
            anomalies.extend(_row_anomalies(source, record))
            cache_key = (
                workbook_index,
                record.input_length,
                record.output_length,
                record.batch_size,
            )
            batch_key = (
                workbook_index,
                record.input_length,
                record.output_length,
                round(record.cache_percentage, 4),
            )
            cache_groups.setdefault(cache_key, []).append(row)
            batch_groups.setdefault(batch_key, []).append(row)

    missing_cache_groups = 0
    for cache_key in sorted(cache_groups):
        rows = _distinct_rows(cache_groups[cache_key], "cache_percentage", limitations)
        if len(rows) < 2:
            missing_cache_groups += 1
            continue
        for baseline, candidate in pairwise(rows):
            trends.append(
                _trend(
                    "cache_percentage",
                    baseline,
                    candidate,
                    "throughput",
                    "t/s",
                    "aggregate throughput",
                    baseline[1].throughput,
                    candidate[1].throughput,
                )
            )

    missing_batch_groups = 0
    for batch_key in sorted(batch_groups):
        rows = _distinct_rows(batch_groups[batch_key], "batch_size", limitations)
        if len(rows) < 2:
            missing_batch_groups += 1
            continue
        for baseline, candidate in pairwise(rows):
            base_source, base_record = baseline
            candidate_source, candidate_record = candidate
            metrics = (
                (
                    "throughput",
                    "t/s",
                    "aggregate throughput",
                    base_record.throughput,
                    candidate_record.throughput,
                ),
                (
                    "throughput_per_box",
                    "t/s/hardware",
                    "per-box throughput",
                    base_record.throughput_per_box,
                    candidate_record.throughput_per_box,
                ),
                ("ttft_ms", "ms", "TTFT", base_record.ttft_ms, candidate_record.ttft_ms),
                (
                    "gen_speed",
                    "t/s/user",
                    "per-user generation speed",
                    base_record.gen_speed,
                    candidate_record.gen_speed,
                ),
                ("rpm", "req/min", "requests per minute", base_record.rpm, candidate_record.rpm),
            )
            trends.extend(
                _trend("batch_size", baseline, candidate, name, unit, label, base_value, cand_value)
                for name, unit, label, base_value, cand_value in metrics
            )
            if (
                base_record.throughput > 0
                and candidate_record.throughput
                < base_record.throughput * (1 - SCALING_DROP_FRACTION)
            ):
                drop = (
                    base_record.throughput - candidate_record.throughput
                ) / base_record.throughput
                anomalies.append(
                    AnomalyFlag(
                        code="ANOMALY_THROUGHPUT_DROP_ON_SCALING",
                        rule=(
                            "Flag an aggregate throughput drop greater than 5% as batch size rises"
                        ),
                        explanation=(
                            f"Batch {base_record.batch_size} to {candidate_record.batch_size}: "
                            f"aggregate throughput fell from {base_record.throughput:g} to "
                            f"{candidate_record.throughput:g} t/s ({drop * 100:.2f}% drop; "
                            "threshold >5%). This is a review signal, not an invalid row."
                        ),
                        sources=[base_source, candidate_source],
                    )
                )

    if missing_cache_groups:
        limitations.append(
            f"No distinct cache-setting partner in {missing_cache_groups} configuration group(s)."
        )
    if missing_batch_groups:
        limitations.append(
            f"No distinct batch-size partner in {missing_batch_groups} configuration group(s)."
        )

    configurations.sort(
        key=lambda item: (
            item.source.model_name,
            item.source.profile_id,
            item.source.workbook_index,
            item.source.record_index,
        )
    )
    trends.sort(
        key=lambda item: (
            item.dimension,
            item.baseline.workbook_index,
            item.baseline.record_index,
            item.candidate.record_index,
            item.metric_name,
        )
    )
    anomalies.sort(
        key=lambda item: (
            item.code,
            item.sources[0].workbook_index,
            item.sources[0].record_index,
            item.explanation,
        )
    )
    return EngineeringAnalysisResponse(
        configurations=configurations,
        trends=trends,
        anomalies=anomalies,
        limitations=limitations,
    )
