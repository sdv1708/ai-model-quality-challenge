"""Tests for the workbook HTTP route."""

import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from perf_api.main import app

CLIENT = TestClient(app)


def test_workbook_normalization_rejects_non_xlsx() -> None:
    """Non-xlsx files return 400 Bad Request."""
    response = CLIENT.post(
        "/api/v1/workbooks/normalize",
        files={
            "workbook": (
                "example.txt",
                b"invalid file content",
                "text/plain",
            )
        },
    )
    assert response.status_code == 400
    assert "Only .xlsx workbook files are supported." in response.json()["detail"]


def test_workbook_normalization_parses_real_sweep() -> None:
    """A valid xlsx sweep from perf_data.zip is normalized into typed records."""
    zip_path = Path(__file__).parents[2] / "perf_data.zip"
    with zipfile.ZipFile(zip_path) as z:
        content = z.read("Model_A_profile_1/Model A profile 1.xlsx")

    response = CLIENT.post(
        "/api/v1/workbooks/normalize",
        files={
            "workbook": (
                "Model A profile 1.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "Model A"
    assert data["profile_id"] == "1"
    assert data["record_count"] == 4
    # Check that forward-filling worked for Input Length, Output Length, Cache %
    first_record = data["records"][0]
    assert first_record["input_length"] == 10000
    assert first_record["output_length"] == 333
    assert first_record["cache_percentage"] == 0.5
    assert first_record["batch_size"] == 10

    fourth_record = data["records"][3]
    assert fourth_record["input_length"] == 10000
    assert fourth_record["output_length"] == 333
    assert fourth_record["cache_percentage"] == 0.5
    assert fourth_record["batch_size"] == 40
