# Issue #6: multi-upload comparison starter

This branch is a **scaffold**, not a completed comparison feature. The new
`POST /api/v1/comparisons/workbooks` route currently returns HTTP 501. The
single-workbook normalization and workload-decision endpoints still work.

Issue: https://github.com/sdv1708/ai-model-quality-challenge/issues/6

## Mental model

Each `.xlsx` file represents one model/profile sweep. Its `Summary` rows are
projected configurations. The existing parser turns file bytes and a filename
into `WorkbookNormalizationResponse`, which contains a `model_name`,
`profile_id`, and typed `PerformanceRecord` rows. Issue #6 composes that parser
for one **or** many files and aligns rows across models. It should never use a
hard-coded list of model names, profile IDs, or batch sizes.

Two projected metric values can be compared directly only when their workload
and configuration dimensions agree. The starter `ConfigurationKey` contains
profile ID, input length, output length, cache fraction, and batch size. A
different key is an explicit coverage gap, not a zero or a losing score.
`is_comparable` should mean at least two distinct models contribute to a key;
`missing_models` should identify other uploaded models without that key. With
only one uploaded model, the same pipeline returns its rows with no pairwise
comparison. Confirm the key policy before coding, especially how to compare
floating cache fractions and whether profile IDs denote equivalent traffic.

Keep customer workload decisions separate from row alignment. Issue #4's
`evaluate_workload` answers whether **one sweep** meets explicit targets; it
may select a different viable batch for each model. A direct metric comparison
should use aligned rows. A customer decision comparison may show model verdicts
side by side, but must disclose differing configurations and missing evidence.
The current scaffold does not choose a cross-model winner.

## Code map

- `src/perf_api/comparison_schemas.py`: response types and comparison key.
- `src/perf_api/comparison.py`: pure alignment function to implement.
- `src/perf_api/routes/comparisons.py`: multipart upload route to implement.
- `src/perf_api/main.py`: registers the route.
- `src/perf_api/parser.py`: existing single-file parser to reuse. Improve it
  only if a concrete comparison case proves the current filename/validation
  rules inadequate.
- `src/perf_api/decision.py`: existing per-sweep decision evaluator; do not
  copy its threshold logic into the comparison function.

## Fill in this order

1. **Define comparability.** Inspect supplied files from at least two models
   and profiles. Write down the canonical key, cache tolerance, model-name
   normalization, duplicate policy, and how a single model is represented.
   Revise `comparison_schemas.py` before wiring the route.
2. **Handle duplicate identity.** In `comparison.py`, identify duplicate
   `(model_name, profile_id)` sweeps and duplicate configuration keys within
   one sweep. Choose a deterministic policy: reject ambiguous duplicates or
   return explicit diagnostics; never silently keep whichever arrived first.
3. **Align records.** Group by canonical key, track each contributing model,
   mark groups with at least two models comparable, and list missing models.
   Preserve the original projected metrics and their units. Do not fill gaps
   with invented numbers.
4. **Make output order stable.** Sort model names, keys, group members, and
   diagnostics. Reversed upload order should yield the same response content.
   Decide whether filename affects diagnostic ordering.
5. **Wire multipart ingestion.** In `routes/comparisons.py`, validate a
   nonempty list of `.xlsx` files, call the existing parser once per file,
   then call the pure comparison function. Pick and document a policy for a
   mixed valid/invalid batch. If rejected, name every failed file and reason
   in the error response. Keep the old one-file route for compatibility.
6. **Write behavior tests.** Use real workbooks through the HTTP test client:
   one file, several supplied models, two profiles, shuffled upload order,
   unseen `Model L`, duplicate sweep, duplicate row key, missing batch/profile,
   and invalid or incomplete workbook. Assert statuses, identities, aligned
   keys, gaps, and diagnostics rather than private helper calls.
7. **Connect the frontend.** Let the file input select multiple files and
   send them in one multipart request. Show comparable groups and coverage
   gaps in both audience views. Keep the current single-upload path working
   until the new route and UI are verified end to end.

## Suggested public request

Repeat the `workbooks` multipart field for each file:

```powershell
curl.exe -F "workbooks=@Model A profile 1.xlsx" `
  -F "workbooks=@Model B profile 1.xlsx" `
  http://127.0.0.1:8000/api/v1/comparisons/workbooks
```

The command currently receives HTTP 501. It becomes a smoke test after step 5.
From `backend/`, run `uv run pytest`, `uv run ruff check .`,
`uv run ruff format --check .`, and `uv run mypy` after implementation slices.
