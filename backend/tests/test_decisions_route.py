"""HTTP contract for the workload decision endpoint."""

from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from perf_api.main import app
from perf_api.parser import parse_and_normalize_workbook

CLIENT = TestClient(app)


@pytest.fixture
def decision_payload() -> dict[str, object]:
    zip_path = Path(__file__).parents[2] / "perf_data.zip"
    with ZipFile(zip_path) as archive:
        workbook_bytes = archive.read("Model_A_profile_1/Model A profile 1.xlsx")
    workbook = parse_and_normalize_workbook(workbook_bytes, "Model A profile 1.xlsx")
    return {
        "workbook": workbook.model_dump(),
        "targets": {"min_throughput_tps": 400_000},
        "assumptions": {},
    }


def test_decision_route_validates_target_units(decision_payload: dict[str, object]) -> None:
    decision_payload["targets"] = {"min_throughput_tps": -1}

    response = CLIENT.post("/api/v1/decisions/evaluate", json=decision_payload)

    assert response.status_code == 422


@pytest.mark.skip(reason="Enable when issue #4 decision rules are implemented")
def test_decision_route_returns_typed_evidence(decision_payload: dict[str, object]) -> None:
    response = CLIENT.post("/api/v1/decisions/evaluate", json=decision_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "go"
    assert body["model_name"] == "Model A"
    assert body["selected_record"] is not None
    assert body["evidence"]
