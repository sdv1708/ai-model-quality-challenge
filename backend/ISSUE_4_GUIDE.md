# Issue #4: workload decision

The workbook parser already returns one `WorkbookNormalizationResponse` containing
`PerformanceRecord` rows. Each row is a projected configuration. Issue #4 turns those
rows and explicit customer targets into a decision that can be explained and tested.
The rules and selection policy are in `src/perf_api/decision.py`.

## Code map

1. `src/perf_api/decision_schemas.py` defines the typed request, row evidence,
   selection explanation, and result contract. Absent targets and assumptions stay `None`.
2. `src/perf_api/decision.py` matches scenarios and checks every constraint on each
   complete row. It returns all matching row evaluations, including failures.
3. `src/perf_api/routes/decisions.py` exposes the pure evaluator through JSON HTTP.
4. `tests/test_decision.py` covers threshold edges, mixed known and unknown facts,
   scenario matching, context, cost, and multi-row evidence. The route tests cover
   validation and JSON serialization.
5. `README.md` documents the request flow, status meanings, and cost limitations.

## Rules to reason through

- `throughput` is aggregate projected tokens per second; `gen_speed` is projected
  generation tokens per second **per user**. They answer different questions.
- `ttft_ms` is time to first token. A threshold is met at equality; make the same
  inclusive-boundary choice for minimum throughput and generation speed.
- Input/output lengths and cache fraction describe the projected scenario. They are
  not proof of a model's maximum context window. An explicitly supplied context
  window must cover both the customer minimum and the row's input plus output tokens.
- A cost ceiling cannot be checked without an explicit hardware price. Any estimate
  derived from `throughput_per_box` is cost at projected capacity, not a quote or
  measured production cost. State the formula and its assumptions in the response.
- Decide and test which status wins when one constraint fails and another is unknown.
  An unknown must never silently count as a pass.
- Preserve the target/actual/unit for each check and every matching row's evidence,
  so a reader can reproduce a global no-go conclusion.

Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and
`uv run mypy` from this directory after each slice.
