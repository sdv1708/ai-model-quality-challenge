# Performance API

This directory contains the Task 1 Python backend. The single-workbook endpoint for
GitHub Issue #2 accepts a performance projection `.xlsx` file and returns normalized,
typed records.

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Set up

```powershell
cd backend
uv sync
```

`uv sync` creates `backend/.venv` and installs both runtime and development dependencies
from `uv.lock`.

## Run locally

```powershell
uv run uvicorn perf_api.main:app --reload
```

Then open:

- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

In the API documentation, use `POST /api/v1/workbooks/normalize` to upload a workbook.
Sample `.xlsx` files are inside the repository's `perf_data.zip`. The endpoint returns
`400` for a filename without the `.xlsx` extension and `422` for an invalid workbook
or invalid workbook data.

## Workload decision scaffold (Issue #4)

`POST /api/v1/decisions/evaluate` accepts JSON with three required objects:
`workbook` (the response from `/api/v1/workbooks/normalize`), `targets`, and
`assumptions`. The target and assumption fields are defined in
`src/perf_api/decision_schemas.py` and shown in `/docs`.

The route is registered, but the learner-owned evaluator in `src/perf_api/decision.py`
is not implemented yet. A valid request currently returns `501 Not Implemented`.
Invalid request fields, such as a negative minimum throughput, return `422`.
Use `ISSUE_4_GUIDE.md` for the implementation order and behavior cases.

TODO (Issue #4): Once implemented, describe how a configuration is selected, what
each status means, the cost formula and its assumptions, and a complete
request/response example. Replace the 501 description with the working behavior.
The workbook values are projections, not production measurements.

## Verify changes

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```
