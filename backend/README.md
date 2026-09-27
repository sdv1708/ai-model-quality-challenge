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

## Verify changes

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```
