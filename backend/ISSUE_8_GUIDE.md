# Issue #8: engineering diagnostics

The [issue](https://github.com/sdv1708/ai-model-quality-challenge/issues/8) asks for an
engineering analysis response over performance projections. The learner owns the
analysis and its tests. This branch supplies the API shape, a pure analysis seam, an
explicit `501` route, and implementation TODOs. It does **not** compute diagnostics.

## What the response must answer

- Which model, profile, input length, output length, cache setting, and batch size
  produced each projected value?
- How do aggregate throughput and per-box throughput compare, in tokens/second
  and tokens/second/hardware respectively?
- How do cached and uncached projections differ for the same configuration?
- What changes when batch size changes while the other configuration dimensions
  stay fixed? How do throughput, TTFT, per-user generation speed, and RPM behave?
- Which rows deserve review, under a named, reproducible rule, and what observed
  values triggered each flag?

These are **projections**, not measured production performance or proof of a
hardware fault. A flag requests review; it does not invalidate a row.

## Concepts and comparison rules

`PerformanceRecord` in `src/perf_api/schemas.py` lists the workbook columns.
`throughput` is aggregate tokens/second; `throughput_per_box` is projected
tokens/second per hardware box. The cached and uncached columns report separate
parts of the projection. In the bundled Model A profile 1 sample, batch 10 has
135,208.3643 uncached and 126,403.1152 cached t/s; their sum is close to the
261,615.7086 total t/s. That pattern suggests a throughput decomposition, **not**
two modes whose ratio measures a cache speedup. Verify the semantics against
the supplied sheets before claiming a causal cache benefit.
`prompt_throughput` and `gen_throughput` distinguish the
prompt-processing and generation phases. `gen_speed` is per-user output speed;
`ttft_ms` is time to first token in milliseconds; `rpm` is requests/minute.
Do not treat these rates as interchangeable or infer a pricing figure from them.

Useful *candidate* derived quantities include:

- **Cache contribution:** report cached and uncached throughput alongside total
  throughput. If total is positive, each component's share can be expressed as
  `component / throughput`, with unit `ratio`. A change in `Cache %` across
  otherwise matching rows can reveal sensitivity, but the columns alone do not
  identify a causal speedup.
- **Aggregate/per-box ratio:** `throughput / throughput_per_box`, only when the
  denominator is positive. It is an implied capacity ratio, not a verified
  physical box count. Check whether the source workbook defines any stronger
  meaning before naming it.
- **Batch effect:** compare rows for the same model, profile, input length,
  output length, and cache setting, changing batch size alone. A percent change
  needs a nonzero baseline. Report both raw values and units even when the
  percent change is unavailable.
- **Scaling:** show changes in aggregate throughput, per-box throughput, TTFT,
  generation speed, and RPM as batch size grows. More aggregate throughput can
  coincide with worse per-user latency. No single rate summarizes all of it.

For cache-setting comparisons across rows, hold model, profile, input length,
output length, and batch size fixed. If no partner row exists, report that
limitation instead of fabricating a trend. Cross-model comparisons require the
alignment rules from issue #6; do not compare unlike workloads as if they were
equivalent. Sort workbooks and rows by stable keys so upload order does not
change results. The supplied Model A profiles have different workload shapes,
so they do not by themselves provide a controlled cache-setting pair.

For example, Model A profile 1 increases projected aggregate throughput from
261,615.7086 t/s at batch 10 to 404,149.0928 t/s at batch 20, while per-user
generation speed falls from 1,354.4772 to 1,220.4817 t/s/user. Both facts
belong in the engineering view; aggregate improvement does not imply every
user-facing metric improves.

The source identity available on `main` is model, profile, and a zero-based index
inside the normalized `records` list. This is **not** an Excel row number. The
parser currently drops filename and worksheet row provenance; the optional
`filename`, `worksheet`, and `sheet_row` fields must stay `None` unless upstream
normalization supplies those facts. Do not reconstruct a sheet row by assuming
all future workbooks have the present layout. Every reported numeric observation
needs its unit and source; ratio units are dimensionless (`ratio`).

Anomaly rules should have a stable code, explicit threshold or comparison, and
an explanation containing the observed values and relevant source rows. Possible
rules to evaluate include nonpositive rates, a large mismatch between total
throughput and its cached-plus-uncached components (if that relationship holds
across the supplied sheets), or a sharp throughput drop between comparable
batch sizes. Select
thresholds and tolerances deliberately, document their limits, and avoid treating
an unusual but valid projection as a parse error. Avoid division by zero and
do not claim a trend when only one point exists.

## Fill-in order

1. **TODO 8.1 — define comparison groups.** Read `schemas.py`, the merged
   issue #6 `comparison_schemas.py` and `comparison.py`, and the sample workbook.
   Decide which dimensions must match for each trend. Write that decision in
   this guide. The request's `workbooks` list can come from issue #6's
   `ComparisonResponse.workbooks`.
2. **TODO 8.2 — preserve and expose source facts.** In `engineering.py`, emit
   one `ConfigurationDiagnostic` per usable input row, retaining its
   `PerformanceRecord`. Add clearly named `EngineeringMetric` values with units
   and an explanation. If filename/sheet provenance is needed, extend the
   normalization path instead of guessing it.
3. **TODO 8.3 — derive comparisons.** Add cache and aggregate/per-box
   observations, then batch and scaling `TrendDiagnostic` values. Handle absent
   partners and zero denominators with a limitation or omitted derived metric,
   never a made-up zero. Keep formulas and units visible.
4. **TODO 8.4 — define anomaly rules.** Give each rule a code, exact condition,
   tolerance, and observed evidence. Flag rows for review without dropping or
   changing them. Repeated calls over the same input must return the same flags.
5. **TODO 8.5 — state limitations.** Explain projection status, missing partners,
   ambiguous workbook semantics, and unavailable provenance in `limitations`.
6. **TODO 8.6 — connect HTTP.** Replace the `501` in
   `routes/engineering.py` with a call to `analyze_engineering`. Keep the
   calculations in the pure module. Feed it the normalized workbooks returned
   by issue #6's `/api/v1/comparisons/workbooks` path.
7. **TODO 8.7 — test public behavior.** Fill in `tests/test_engineering.py` with
   representative scaling, cache, per-box, and anomaly cases. Check exact
   sources, units, explanations, deterministic order, absent comparison rows,
   and unusual valid values. Include an HTTP test for the final response.

## Run the scaffold

From `backend`:

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run uvicorn perf_api.main:app --reload
```

`POST /api/v1/engineering/analyze` accepts `{"workbooks": [<normalized
workbook>, ...]}`. Until TODO 8.6 is complete, a valid request returns `501`
with a clear message. `/docs` shows the intended request and response models.
