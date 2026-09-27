"""Tests for the application health boundary."""

from fastapi.testclient import TestClient

from perf_api.main import app


def test_health_reports_ready_service() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "perf-api"}
