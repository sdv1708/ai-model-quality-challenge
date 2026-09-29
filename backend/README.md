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

## Workload decisions (Issue #4)

`POST /api/v1/decisions/evaluate` accepts JSON with three required objects:
`workbook` (the response from `/api/v1/workbooks/normalize`), `targets`, and
`assumptions`. The target and assumption fields are defined in
`src/perf_api/decision_schemas.py` and shown in `/docs`.

The response returns `go` when a matching configuration meets every check,
`no_go` when every matching configuration has a known failure, and
`insufficient_data` when a potentially passing configuration depends on missing
facts or no row matches the requested scenario. With no thresholds, there is no
decision. Threshold equality counts as meeting a limit. Each result includes a
representative row, its evidence, an explanation of its selection, and evidence
for **every** matching configuration. Ties follow workbook row order.

The context check compares an explicitly supplied context window with both the
customer's minimum and the projected row's input plus output length. A workbook
scenario does not prove the model's maximum supported context. Cost requires an
explicit box-hour price and positive projected throughput per box. The estimate is:

```text
USD per million projected throughput tokens =
    box-hour price * 1,000,000 / (throughput_per_box * 3,600)
```

This is a hardware-only estimate at sustained projected capacity. It excludes
idle time and other costs; it is not a customer quote or production measurement.
Missing price or unusable per-box throughput produces `unknown` cost evidence.
Invalid request fields, such as a negative minimum throughput, return `422`.

With the server running, this PowerShell example normalizes the bundled sample
and evaluates a workload through the public endpoints:

```powershell
$sample = (Resolve-Path '../frontend/public/sample/Model A profile 1.xlsx').Path
$workbook = curl.exe -sS -F "workbook=@$sample" `
    'http://127.0.0.1:8000/api/v1/workbooks/normalize' | ConvertFrom-Json
$body = @{
    workbook = $workbook
    targets = @{
        input_tokens = 10000
        output_tokens = 333
        cache_fraction = 0.5
        min_throughput_tps = 400000
        min_generation_speed_tps_per_user = 1200
        max_ttft_ms = 10
    }
    assumptions = @{}
} | ConvertTo-Json -Depth 8
$result = Invoke-RestMethod -Method Post `
    -Uri 'http://127.0.0.1:8000/api/v1/decisions/evaluate' `
    -ContentType 'application/json' -Body $body
$result | Select-Object status, selection_explanation, unmet_constraints, unknown_constraints
$result.selected_record.batch_size
$result.evidence | Format-Table metric, outcome, actual, target, unit
```

The sample yields `go` with batch size `20` and three met checks. The values
remain workbook projections, not measured production performance. See
`ISSUE_4_GUIDE.md` for the code map and test cases.

## Compare one or many workbooks (Issue #6)

`POST /api/v1/comparisons/workbooks` accepts repeated `workbooks` multipart
fields. It runs every file through the existing parser, then aligns projected
rows by profile, input and output lengths, cache fraction, and batch size.
The response lists models, normalized workbooks, aligned configurations,
missing models, and diagnostics. One file uses the same path and has no
pairwise-comparable rows.

Identical repeated model/profile sweeps are compared once with a diagnostic.
Conflicting sweeps and sweeps with duplicate configuration rows are excluded;
they are never resolved by upload order. A mixed batch returns its
usable comparisons and file-specific diagnostics. If no usable configuration
remains, the endpoint returns `422` with diagnostics in `detail`. See
`ISSUE_6_GUIDE.md` for the comparison policy and test cases.

## Verify changes

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```
