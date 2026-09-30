"""Public behavior of the issue #8 engineering response and endpoint."""

from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from perf_api.engineering import analyze_engineering
from perf_api.main import app
from perf_api.parser import parse_and_normalize_workbook
from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse

SAMPLE_WORKBOOK = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "public"
    / "sample"
    / "Model A profile 1.xlsx"
)


def record(**changes: int | float) -> PerformanceRecord:
    """Build one coherent projected row; callers override only the fields under test."""
    values: dict[str, int | float] = {
        "input_length": 100,
        "output_length": 100,
        "cache_percentage": 0.5,
        "batch_size": 10,
        "max_ms": 500,
        "target_max_ms": 600,
        "prompt_throughput": 150,
        "gen_throughput": 110,
        "throughput": 260,
        "throughput_per_box": 26,
        "uncached_throughput": 130,
        "uncached_throughput_per_box": 13,
        "cached_throughput": 130,
        "cached_throughput_per_box": 13,
        "ttft_ms": 12.5,
        "real_prompt_speed": 1500,
        "prompt_speed_queued": 1400,
        "gen_speed": 1350,
        "rpm": 6000,
    }
    values.update(changes)
    return PerformanceRecord.model_validate(values)


def workbook(*rows: PerformanceRecord, model: str = "Model A") -> WorkbookNormalizationResponse:
    return WorkbookNormalizationResponse(
        model_name=model,
        profile_id="1",
        record_count=len(rows),
        records=list(rows),
    )


@pytest.fixture
def batch_sweep() -> WorkbookNormalizationResponse:
    return workbook(
        record(),
        record(
            batch_size=20,
            throughput=400,
            throughput_per_box=40,
            cached_throughput=200,
            uncached_throughput=200,
            cached_throughput_per_box=20,
            uncached_throughput_per_box=20,
            ttft_ms=25,
            gen_speed=1220,
            rpm=10000,
        ),
    )


def test_configurations_keep_source_and_report_units(
    batch_sweep: WorkbookNormalizationResponse,
) -> None:
    response = analyze_engineering([batch_sweep])

    assert len(response.configurations) == 2
    first = response.configurations[0]
    assert first.source.model_name == "Model A"
    assert first.source.profile_id == "1"
    assert (first.source.workbook_index, first.source.record_index) == (0, 0)
    assert first.source.filename is None
    assert first.record == batch_sweep.records[0]
    metrics = {metric.name: metric for metric in first.metrics}
    assert metrics["throughput"].value == 260
    assert metrics["throughput"].unit == "t/s"
    assert metrics["cached_throughput"].value == 130
    assert metrics["uncached_throughput_per_box"].unit == "t/s/hardware"
    assert metrics["cached_share"].value == pytest.approx(0.5)
    assert metrics["cached_share"].unit == "ratio"
    assert metrics["implied_box_capacity_ratio"].value == pytest.approx(10)
    assert "not a verified physical box count" in metrics["implied_box_capacity_ratio"].explanation


def test_batch_scaling_reports_all_five_metrics(
    batch_sweep: WorkbookNormalizationResponse,
) -> None:
    response = analyze_engineering([batch_sweep])
    trends = {
        trend.metric_name: trend for trend in response.trends if trend.dimension == "batch_size"
    }

    assert set(trends) == {"throughput", "throughput_per_box", "ttft_ms", "gen_speed", "rpm"}
    assert (trends["throughput"].baseline_value, trends["throughput"].candidate_value) == (
        260,
        400,
    )
    assert trends["throughput_per_box"].unit == "t/s/hardware"
    assert trends["ttft_ms"].unit == "ms"
    assert trends["gen_speed"].candidate_value == 1220
    assert trends["gen_speed"].unit == "t/s/user"
    assert trends["rpm"].unit == "req/min"
    assert trends["throughput"].baseline.record_index == 0
    assert trends["throughput"].candidate.record_index == 1
    assert "Batch size 10 to 20" in trends["throughput"].explanation


def test_cache_setting_uses_fraction_as_percentage() -> None:
    lower = record(
        cache_percentage=0.25,
        throughput=200,
        throughput_per_box=20,
        cached_throughput=50,
        uncached_throughput=150,
    )
    higher = record(
        cache_percentage=0.75,
        throughput=300,
        throughput_per_box=30,
        cached_throughput=200,
        uncached_throughput=100,
    )
    response = analyze_engineering([workbook(lower, higher)])

    cache_trends = [trend for trend in response.trends if trend.dimension == "cache_percentage"]
    assert len(cache_trends) == 1
    assert (cache_trends[0].baseline_value, cache_trends[0].candidate_value) == (200, 300)
    assert "Cache setting 25% to 75%" in cache_trends[0].explanation
    assert cache_trends[0].unit == "t/s"
    assert not any(flag.code == "ANOMALY_THROUGHPUT_MISMATCH" for flag in response.anomalies)


def test_supplied_sample_rounding_does_not_raise_false_mismatch() -> None:
    normalized = parse_and_normalize_workbook(SAMPLE_WORKBOOK.read_bytes(), SAMPLE_WORKBOOK.name)
    response = analyze_engineering([normalized])

    assert len(response.configurations) == 4
    assert not any(flag.code == "ANOMALY_THROUGHPUT_MISMATCH" for flag in response.anomalies)


def test_decomposition_tolerance_matches_supplied_sweeps() -> None:
    archive_path = Path(__file__).resolve().parents[2] / "perf_data.zip"
    with ZipFile(archive_path) as archive:
        workbooks = [
            parse_and_normalize_workbook(archive.read(name), Path(name).name)
            for name in archive.namelist()
            if name.endswith(".xlsx")
        ]

    response = analyze_engineering(workbooks)
    assert len(response.configurations) == 275
    assert not any(flag.code == "ANOMALY_THROUGHPUT_MISMATCH" for flag in response.anomalies)


def test_large_decomposition_mismatch_explains_rule_and_source() -> None:
    response = analyze_engineering([workbook(record(cached_throughput=30))])
    mismatch = next(
        flag for flag in response.anomalies if flag.code == "ANOMALY_THROUGHPUT_MISMATCH"
    )

    assert "0.1%" in mismatch.rule
    assert "0.01 t/s" in mismatch.rule
    assert "absolute difference is 100 t/s" in mismatch.explanation
    assert [(source.workbook_index, source.record_index) for source in mismatch.sources] == [(0, 0)]
    assert len(response.configurations) == 1  # Flagging does not discard the row.


def test_zero_baseline_retains_raw_trend_without_fake_percentage() -> None:
    zero = record(
        throughput=0,
        throughput_per_box=0,
        cached_throughput=0,
        uncached_throughput=0,
    )
    positive = record(batch_size=20, throughput=100, throughput_per_box=10)
    response = analyze_engineering([workbook(zero, positive)])
    throughput_trend = next(
        trend
        for trend in response.trends
        if trend.dimension == "batch_size" and trend.metric_name == "throughput"
    )

    assert throughput_trend.baseline_value == 0
    assert throughput_trend.candidate_value == 100
    assert "percent change unavailable" in throughput_trend.explanation
    assert "0.00%" not in throughput_trend.explanation
    assert all(metric.name != "cached_share" for metric in response.configurations[0].metrics)


def test_unusual_value_is_flagged_and_retained() -> None:
    response = analyze_engineering([workbook(record(ttft_ms=0))])

    assert len(response.configurations) == 1
    flag = next(flag for flag in response.anomalies if flag.code == "ANOMALY_NONPOSITIVE_METRIC")
    assert "ttft_ms=0 ms" in flag.explanation
    assert flag.sources[0].record_index == 0


def test_batch_drop_rule_has_threshold_and_pair_sources() -> None:
    rows = workbook(
        record(throughput=100, cached_throughput=50, uncached_throughput=50),
        record(
            batch_size=20,
            throughput=95,
            cached_throughput=45,
            uncached_throughput=50,
        ),
        record(
            batch_size=30,
            throughput=89,
            cached_throughput=39,
            uncached_throughput=50,
        ),
    )
    response = analyze_engineering([rows])
    drops = [
        flag for flag in response.anomalies if flag.code == "ANOMALY_THROUGHPUT_DROP_ON_SCALING"
    ]

    assert len(drops) == 1  # Exactly 5% from 100 to 95 does not trigger >5%.
    assert [source.record_index for source in drops[0].sources] == [1, 2]
    assert "greater than 5%" in drops[0].rule
    assert "6.32% drop" in drops[0].explanation


def test_missing_and_repeated_partners_are_not_invented() -> None:
    response = analyze_engineering([workbook(record(), record())])

    assert response.trends == []
    assert len(response.configurations) == 2
    assert any("Repeated cache_percentage" in item for item in response.limitations)
    assert any("No distinct cache-setting partner" in item for item in response.limitations)
    assert any("No distinct batch-size partner" in item for item in response.limitations)


def test_duplicate_identifiers_are_stable_across_upload_order() -> None:
    first = workbook(record(), model="Model A")
    second = workbook(
        record(
            throughput=300,
            throughput_per_box=30,
            cached_throughput=150,
            uncached_throughput=150,
            cached_throughput_per_box=15,
            uncached_throughput_per_box=15,
        ),
        model="Model A",
    )

    forward = analyze_engineering([first, second]).model_dump()
    backward = analyze_engineering([second, first]).model_dump()

    assert forward == backward
    assert {cfg["source"]["workbook_index"] for cfg in forward["configurations"]} == {0, 1}


def test_http_endpoint_returns_analysis_and_validates_empty_request(
    batch_sweep: WorkbookNormalizationResponse,
) -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/engineering/analyze",
        json={"workbooks": [batch_sweep.model_dump()]},
    )

    assert response.status_code == 200
    assert len(response.json()["configurations"]) == 2
    assert len(response.json()["trends"]) == 5
    assert client.post("/api/v1/engineering/analyze", json={"workbooks": []}).status_code == 422


def test_comparison_upload_can_feed_engineering_endpoint() -> None:
    client = TestClient(app)
    compared = client.post(
        "/api/v1/comparisons/workbooks",
        files={"workbooks": (SAMPLE_WORKBOOK.name, SAMPLE_WORKBOOK.read_bytes())},
    )
    assert compared.status_code == 200

    analyzed = client.post(
        "/api/v1/engineering/analyze",
        json={"workbooks": compared.json()["workbooks"]},
    )
    assert analyzed.status_code == 200
    assert len(analyzed.json()["configurations"]) == 4
