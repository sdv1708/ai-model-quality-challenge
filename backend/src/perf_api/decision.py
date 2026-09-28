"""Customer workload decisions derived from normalized workbook projections."""

from perf_api.decision_schemas import DecisionAssumptions, WorkloadDecision, WorkloadTargets
from perf_api.schemas import WorkbookNormalizationResponse


def evaluate_workload(
    workbook: WorkbookNormalizationResponse,
    targets: WorkloadTargets,
    assumptions: DecisionAssumptions,
) -> WorkloadDecision:
    """Return a traceable go/no-go/insufficient-data result for one workbook.

    Implementation contract:

    1. Treat input_tokens, output_tokens, and cache_fraction as the requested
       scenario. Match them to complete workbook rows; do not interpolate or
       silently use a row for a different scenario. With no matching row, there
       is insufficient data rather than proof that the model cannot serve it.
    2. For each eligible row, compare every supplied speed threshold on that
       same row: throughput >= minimum, gen_speed >= per-user minimum, and
       ttft_ms <= maximum. Equality meets a threshold. Never combine the best
       metric values from different rows.
    3. Check a context target only when context_window_tokens was explicitly
       supplied. Workbook input/output lengths describe projected scenarios;
       they do not establish the model's maximum context window.
    4. Check a cost ceiling only when hardware_cost_usd_per_box_hour was supplied
       and the row has positive throughput_per_box. A possible capacity-only
       estimate is price_per_box_hour * 1_000_000 /
       (throughput_per_box * 3_600). Label the token basis and assumptions;
       this is neither a customer quote nor measured production cost.
    5. A go requires one eligible row meeting every supplied constraint. A
       no_go needs evidence that no eligible row can satisfy them. Return
       insufficient_data for absent targets, unmatched scenarios, or unknown
       facts that could change the verdict. Define and test mixed fail/unknown
       precedence explicitly.
    6. Choose a representative row deterministically and explain that choice.
       Return target, actual, unit, and met/unmet/unknown for each requested
       check. Keep unmet_constraints separate from unknown_constraints and
       state every supplied assumption plus the projection limitation.

    The skipped behavior tests in tests/test_decision.py provide first cases to
    enable one at a time as these rules are implemented.
    """
    # TODO(issue #4): Match the requested scenario to complete workbook rows.
    # TODO(issue #4): Evaluate all supplied constraints for each eligible row.
    # TODO(issue #4): Select one row and derive status without hiding unknowns.
    # TODO(issue #4): Return evidence, unmet/unknown lists, and assumptions.
    raise NotImplementedError("Implement issue #4 workload decision rules")
