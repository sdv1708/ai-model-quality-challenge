# Issue #8: engineering diagnostics

The [issue](https://github.com/sdv1708/ai-model-quality-challenge/issues/8) asks for an
engineering analysis response over performance projections. The learner owns the
analysis and its tests. This branch supplies the API shape, pure analysis
function, HTTP route, and behavior tests.

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

The source identity is model, profile, a zero-based index in the deterministically
sorted workbook list, and a zero-based index inside each normalized `records`
list. The record index is **not** an Excel row number. The
parser currently drops filename and worksheet row provenance; the optional
`filename`, `worksheet`, and `sheet_row` fields must stay `None` unless upstream
normalization supplies those facts. Do not reconstruct a sheet row by assuming
all future workbooks have the present layout. Every reported numeric observation
needs its unit and source; ratio units are dimensionless (`ratio`).

The anomaly rules are deterministic review signals:

- Aggregate or per-box throughput, TTFT, or generation speed at or below zero
  is flagged. Zero TTFT occurs in one supplied row, so this is a review signal.
- Cached plus uncached throughput is compared with total using both a 0.1%
  relative tolerance and a 0.01 t/s absolute tolerance. A flag requires the
  difference to exceed both. All 275 supplied rows are within the relative
  tolerance; the largest relative difference is about 0.0192%. The apparent
  decomposition is inferred from the supplied projections, not a guaranteed
  workbook invariant.
- A batch step is flagged when aggregate throughput drops by **more than 5%**
  from a positive baseline. This is a review heuristic. A zero or negative
  baseline has no meaningful percent change; raw values remain visible.

No anomaly rule removes or changes a source row.

## Implementation map

1. `engineering_schemas.py` defines the sourced response. `SourceReference`
   includes a stable workbook index so duplicate model/profile names do not
   make source references collide.
2. `engineering.py` groups rows within each workbook. Cache-setting trends
   hold input length, output length, and batch size fixed. Batch trends hold
   input length, output length, and cache fraction fixed. Equal values are not
   described as changes. Five batch metrics are compared.
3. `routes/engineering.py` accepts normalized workbooks returned by issue #6's
   `/api/v1/comparisons/workbooks` route and calls the pure analysis function.
   Pydantic rejects an empty `workbooks` list with HTTP `422`.
4. `tests/test_engineering.py` covers units, source references, batch metrics,
   cache fractions, zero baselines, anomaly thresholds, duplicate identities,
   supplied workbooks, and the HTTP route.

Filename and worksheet-row provenance still require an upstream normalization
contract change. Until then those optional source fields remain `None`.

## Run and verify

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
workbook>, ...]}` and returns sourced configurations, trends, anomaly flags,
and limitations. `/docs` shows the request and response models.
