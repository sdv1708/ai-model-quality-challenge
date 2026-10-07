# Issue #10: your backend work

Work on `feature/issue-10-resilience`. The assistant owns the frontend, browser
journeys, responsive behavior and accessibility checks. The workbook fixture
factory and public API assertions below are now implemented and reviewed.
Verification: 56 backend tests passed, including all eight issue #10 cases;
Ruff and mypy passed. These sections preserve the learning/verification order.

## 1. Fresh workbook bytes — TODO10-01

Fill `build_valid_workbook_bytes()` in `tests/resilience_fixtures.py`.

- Create a real openpyxl workbook with a `Summary` sheet.
- Put the 19 documented headers on row 2 and two numeric data rows from row 3.
- Give A and L matching configurations with different performance values.
- Save to `BytesIO` and return bytes. The upload filename supplies model/profile
  identity. Do not load or rename shipped Model A bytes.
- Choose exact expected values independently. Use numeric cells, not formulas.

The contract is documented in `src/perf_api/parser.py` and
`src/perf_api/schemas.py`. Cache 0.5 means 50%, throughput is tokens/second,
TTFT is milliseconds, and generation speed is tokens/second/user.

For an example, use `(input=100, output=100, cache=0.5, batch=10/20)`, with A
capacities 260/400 and L capacities 520/800. A capacity target of 450 distinguishes
the customer verdicts. You can choose other values; assert your chosen values.
Keep cached/uncached and per-box components coherent.

## 2. Malformed workbook bytes — TODO10-02

Fill `build_malformed_workbook_bytes()` in the same file. Start from a generated
valid workbook and introduce one failure per variant:

- `missing-column`: remove the Batch Size header.
- `invalid-number`: put a string in the first Batch Size data cell.
- `empty-table`: keep the sheet/headers with no data rows.

Corrupt archive bytes are a separate input. The export helper is optional for
inspecting your generated files. Frontend tests generate their own independent
fixtures automatically; they do not depend on completing your factory.

## 3. Public API assertions — TODO10-03

Complete `tests/test_resilience.py`. Remove its module skip and each unfinished
exception as the corresponding assertions become complete.

| TODO | What to prove |
|---|---|
| 03a | Fresh Model L preserves exact values; customer and engineering APIs use them and retain source identity. |
| 03b | A+L and L+A produce identical aligned responses with distinct model metrics. Missing configurations remain gaps. |
| 03c | Missing-header, invalid-number, empty and corrupt files return specific `422` diagnostics naming the file/problem. |
| 03d | A mixed valid/invalid batch returns `200`, retains Model L and names the rejected file. |

Use `POST /api/v1/comparisons/workbooks` with repeated multipart `workbooks`
fields. Its error `detail` is a diagnostic list. The single normalization route
uses a different error contract.

Call `/api/v1/decisions/evaluate` with `workbook`, explicit `targets` and
`assumptions`; call `/api/v1/engineering/analyze` with a `workbooks` array.
Check evidence/metrics, not just status codes. Record indices are zero-based;
Excel row numbers in parse errors refer to worksheet coordinates.

## Verify

From the `backend` directory:

```powershell
uv run pytest tests/test_resilience.py -rs
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Current tests have no skipped cases. Results and fixture values are recorded in
`../docs/issue-10-evidence.md`. Change production backend behavior only when a test
identifies an actual gap.

## What the review fixed

`Worksheet.cell()` accepts `value=`, not `values=`. The extra letter caused a
TypeError before the workbook could be serialized or uploaded.

`sheet.cell(..., value=None)` does not clear an existing value in openpyxl. It
returns the cell and leaves its existing contents intact. Assigning
`sheet.cell(...).value = None` actually removes the header. This distinction
matters: an invalid-input test must genuinely construct an invalid workbook.

The response helper now declares an HTTP response type, malformed case names use
their Literal union, and openpyxl imports follow the repository's existing narrow
`import-untyped` convention. The rest of strict type checking remains enabled.
