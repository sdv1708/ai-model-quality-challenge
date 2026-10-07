# Issue #10: Model L and Task 1 resilience

[GitHub issue](https://github.com/sdv1708/ai-model-quality-challenge/issues/10)

The learner owns backend workbook generation and API assertions. The assistant
owns all frontend work. Your remaining checklist is
[`backend/ISSUE_10_BACKEND_GUIDE.md`](backend/ISSUE_10_BACKEND_GUIDE.md).

Backend fixtures/assertions are implemented and verified: 56 tests pass with no
skips, including eight issue #10 cases. The built-frontend suite has 28 passing
tests with no skips, including a journey using the learner's exported workbook
bytes. It also retains independent browser fixtures. Current verification and
manual audit limitations are recorded in `docs/issue-10-evidence.md`. The issue
stays open until all acceptance evidence exists.

## What you are proving

The product already parses uploads, aligns models, evaluates customer constraints,
and exposes engineering diagnostics. Now prove those features operate on new data
and remain usable when uploads or network requests fail. Issue #9 is closed, so this
issue is unblocked. Deployment is the following issue, #11.

The five acceptance criteria are:

1. A freshly generated conforming Model L renders without application code changes.
2. Multiple uploads work through a built frontend and the real backend.
3. Malformed files produce specific errors and permit recovery.
4. End-to-end tests cover comparison, customer, and engineering journeys.
5. Automated accessibility checks and a manual keyboard pass succeed.

## Concepts and technical details

### Workbook contract and independent fixtures

An `.xlsx` file is a ZIP-based Excel workbook, not JSON with an Excel extension.
Use openpyxl to create real workbook bytes, serialize to `BytesIO`, and upload
those bytes. `Summary` is required; its headers are on row 2 and data begins on
row 3. See `backend/src/perf_api/parser.py` for all 19 source headers and
`backend/src/perf_api/schemas.py` for their normalized names and numeric types.

Input/output lengths and batch size are integers. Performance fields are floats;
the cache value is a fraction (0.5 means 50%), throughput is tokens/second,
TTFT is milliseconds, generation speed is tokens/second/user, and RPM is
requests/minute. The parser carries forward input length, output length and cache
share when their later cells are blank. Other required fields must have values.
The normalized response contains `model_name`, `profile_id`, `record_count`, and
`records`. Identity currently comes from the filename, e.g.
`Model L profile 1.xlsx`; the model does not need a registration entry.

Create headers explicitly from the documented contract. Do not ask the production
parser to supply expected outputs: the fixture should independently challenge it.
Give A and L two rows each, sharing configuration keys but differing in metrics.
Pick and record exact expected values before writing assertions. Keep performance
components coherent: cached + uncached = aggregate, and per-box components sum to
per-box throughput. Synthetic values prove software behavior, not actual Model L
performance. Use numeric cells rather than formulas: the parser uses
`data_only=True` and openpyxl does not calculate formula results.

Existing Model L checks rename shipped Model A bytes. They provide useful evidence
for dynamic naming. This issue strengthens the evidence by generating new rows
and verifying exact values in both the API and rendered views. Repeatability here
means stable row values and conclusions; Excel archive bytes need not have the
same hash because metadata may vary.

### HTTP and the actual upload path

The browser puts each file in `FormData` under repeated `workbooks` fields and
posts to `/api/v1/comparisons/workbooks`. This is multipart form data; do not set
its Content-Type manually, because the browser supplies the boundary. The backend
parses every file, then aligns the usable normalized workbooks.

Alignment keys are profile ID, input length, output length, cache fraction and
batch size. Different performance values do not prevent alignment. Missing
members are coverage gaps; they are not zero throughput. Upload order must not
change the comparison result. Duplicate/conflicting sweep policies already have
coverage in `backend/tests/test_comparisons.py`.

After comparison, customer evaluation posts normalized data and explicit
`targets`/`assumptions` to `/api/v1/decisions/evaluate`. A useful generated-data
test chooses a capacity threshold between the A and L values, obtains different
verdicts, and verifies the evidence, not just the heading. `go` means a matching
row meets the checks, `no_go` means every matching row has a known failure, and
`insufficient_data` means a potentially passing outcome depends on missing facts
or no matching scenario exists. Empty thresholds do not establish a decision.

Engineering analysis posts a `workbooks` array to
`/api/v1/engineering/analyze`. Verify metric values, units and source identity:
model, profile, workbook index and record index. UI normalized row numbers are
record index + 1; they are distinct from Excel worksheet row numbers. A validation
error mentioning Excel row 3 refers to the first data row.

### Failure scopes and recovery

The comparison endpoint returns `200` plus diagnostics when some usable data
remains. It returns `422` with a diagnostic list in `detail` when no usable
configuration remains. Unsupported extensions produce `INVALID_FILE_TYPE`;
parse failures produce `PARSER_ERROR`. The single normalization endpoint has a
different contract: unsupported extensions return `400` and parse errors return
`422` with a string detail. Assert the endpoint actually used by the browser.

Test a missing header, invalid numeric cell, empty data table and corrupt archive
independently. A malformed worksheet and a network failure are different errors:
the latter has no HTTP response. Playwright can abort one upload request to
simulate a connection failure, then remove interception so recovery uses the
real API. Mocking every success response would bypass the evidence you need.

Recovery means the explanation names the relevant file/problem, controls become
usable again, a new upload succeeds without a reload, and results belong to the
new upload. Also try valid -> invalid -> valid. The current application clears
the comparison at the start of an upload; preserve that visible behavior unless
you explicitly decide to change it. Mixed-batch warnings can coexist with usable
views and are rendered differently from fatal `role="alert"` errors.

### Testing layers and the built frontend

`pytest` + FastAPI `TestClient` exercise HTTP routes in process. They prove parsing,
status codes, diagnostics and response data, but cannot prove browser rendering,
fetch routing or focus behavior. Playwright drives Chromium through the actual
file picker and real API. Use role/label locators and Playwright's auto-waiting
assertions instead of arbitrary sleeps.

The normal Playwright config runs Vite's dev server. The new
`frontend/playwright.resilience.config.ts` serves compiled `dist` via Vite preview
on port 4174 and the backend on 8018. All existing specs run there as well as the
new scaffolds. Run the build explicitly first so you test the latest source.
The preview proxy forwards `/api` to the real backend on 8018, exercising a
same-origin deployment arrangement. `reuseExistingServer: false` prevents an old
server from quietly becoming your evidence.

`VITE_API_BASE_URL` is embedded at build time. Leave it unset for this local proxy
check. A separately deployed frontend/API pair has different origins and needs
backend CORS configuration; this local check does not prove that topology or
public reachability. Vite preview is a local test server. Issue #11 establishes
the real host and live smoke tests.

### Accessibility and responsive behavior

`@axe-core/playwright` scans the rendered DOM. The scaffold checks WCAG 2 A/AA
and WCAG 2.1 A/AA tagged rules. Scan settled empty, comparison, customer-result,
engineering and error states; add the mixed-batch state if needed. Fix actual
semantics, labels or contrast in the source. Do not hide violations with broad
exclusions. A clean scan is evidence for the scanned rules/states, not a claim of
complete accessibility conformance.

A manual keyboard pass checks things automation cannot fully assess: sensible
Tab/Shift+Tab order, visible focus, native activation, no traps, useful focus
after errors, and reaching scrollable table contents. Test at 390px width and
at browser zoom 200%. Tables may scroll inside their containers; the whole page
should not overflow sideways and controls should remain operable. Record what
you actually observed, including failures, in the evidence file.

## Backend implementation order and frontend ownership

| Order / TODO | File | Work and completion signal |
|---|---|---|
| 1 / Complete | `backend/tests/resilience_fixtures.py` | Fresh A/L bytes, explicit expected values, normalization verified. |
| 2 / Complete | Same file | Missing-header, invalid-number and empty-table mutations; export verified. |
| 3 / Complete | `backend/tests/test_resilience.py` | Eight public API cases pass with no skips, including values, alignment, gaps and diagnostics. |
| Assistant | Frontend configs and browser tests | Built-bundle journeys, recovery, responsive behavior and axe checks are implemented; frontend tasks are not assigned to the learner. |
| Verification | `docs/issue-10-evidence.md` | Current fixture values, backend results and browser results recorded. |

`frontend/tests/support/resilience.ts` supplies generated fixture paths and a
shared upload action. Frontend-owned fixtures are generated by
`frontend/tests/support/generate_browser_fixtures.py` through Playwright global
setup, under `frontend/tests/fixtures/browser-generated/`. The learner's optional
export writes to the separate `fixtures/generated/` folder, now also generated
by global setup and uploaded by a dedicated browser journey. Both are ignored by
Git and neither is shipped as public sample data. No production parser/decision
changes are preselected: make targeted fixes only when a backend test demonstrates
a problem.

## Commands

From the repository root, install backend dependencies if needed:

```powershell
cd backend
uv sync
```

After TODO10-01/02, while in `backend`:

```powershell
uv run python tests/resilience_fixtures.py
uv run pytest tests/test_resilience.py -rs
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

From the repository root, in a separate terminal:

```powershell
cd frontend
npm ci
npx playwright install chromium
npm run build
npm run test:e2e:built
```

The backend factory and all new API cases are implemented and enabled. Both
fixture sets regenerate automatically. The built suite rebuilds dist first with
local API settings, so a stale bundle or inherited deployment URL cannot change
the tested backend. To run only the new frontend specs:

```powershell
npm run test:e2e:built -- tests/resilience.spec.ts tests/accessibility.spec.ts
```

For a manual check, start backend 8018 and preview yourself in separate terminals:

```powershell
# Terminal 1, backend directory
uv run uvicorn perf_api.main:app --host 127.0.0.1 --port 8018
```

```powershell
# Terminal 2, frontend directory (build first)
$env:VITE_DEV_API_TARGET = 'http://127.0.0.1:8018'
npm run preview -- --port 4174 --strictPort
```

Open http://127.0.0.1:4174 and follow the evidence checklist. Stop those servers
before Playwright runs, because its configuration starts its own servers.

## Definition of done

All five acceptance criteria have recorded evidence. Every intended new test is
enabled, unfinished exceptions are removed, existing tests still pass, fixtures
regenerate from a clean checkout, and the manual pass has real observations.
Keep public deployment claims for issue #11. Do not close #10 merely because the
scaffold or a suite with skipped acceptance tests is green.
