# Issue #4: workload decision

The workbook parser already returns one `WorkbookNormalizationResponse` containing
`PerformanceRecord` rows. Each row is a projected configuration. Issue #4 turns those
rows and explicit customer targets into a decision that can be explained and tested.

## Fill these files in order

1. `src/perf_api/decision_schemas.py`: review the target names, units, and result
   vocabulary before implementing rules. Keep absent values as `None`; do not choose a
   customer workload or hardware price on the caller's behalf.
2. `tests/test_decision.py`: remove one skip marker at a time and make that behavior
   pass. Add just below/above threshold cases and small hand-written workbooks for edge
   cases the bundled sample does not cover.
3. `src/perf_api/decision.py`: replace the placeholder with row matching, per-row
   comparisons, an explicit status policy, and evidence. Evaluate all constraints on the
   **same** row. Keep unresolved constraints distinct from failed ones.
4. `src/perf_api/routes/decisions.py` and `src/perf_api/main.py`: review the registered
   JSON route after the pure function works. Keep HTTP concerns out of `decision.py`.
5. `tests/test_decisions_route.py` and `README.md`: remove the route test skip, verify
   the API response, and document a real request, the projection caveat, and any cost
   formula used.

## Rules to reason through

- `throughput` is aggregate projected tokens per second; `gen_speed` is projected
  generation tokens per second **per user**. They answer different questions.
- `ttft_ms` is time to first token. A threshold is met at equality; make the same
  inclusive-boundary choice for minimum throughput and generation speed.
- Input/output lengths and cache fraction describe the projected scenario. They are
  not proof of a model's maximum context window. Check an explicit context-window
  assumption when a context threshold is supplied.
- A cost ceiling cannot be checked without an explicit hardware price. Any estimate
  derived from `throughput_per_box` is cost at projected capacity, not a quote or
  measured production cost. State the formula and its assumptions in the response.
- Decide and test which status wins when one constraint fails and another is unknown.
  An unknown must never silently count as a pass.
- Preserve the selected row and the target/actual/unit for each check, so a reader can
  reproduce the conclusion without trusting a summary label.

Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and
`uv run mypy` from this directory after each slice.
