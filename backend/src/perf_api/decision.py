"""Customer workload decisions derived from normalized workbook projections."""

import math
from typing import TypedDict

from perf_api.decision_schemas import (
    ConfigurationEvaluation,
    ConstraintEvidence,
    DecisionAssumptions,
    MetricName,
    WorkloadDecision,
    WorkloadTargets,
)
from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse


class EvaluatedRow(TypedDict):
    record: PerformanceRecord
    evidence: list[ConstraintEvidence]
    unmet: list[MetricName]
    unknown: list[MetricName]
    is_go: bool


def evaluate_workload(
    workbook: WorkbookNormalizationResponse,
    targets: WorkloadTargets,
    assumptions: DecisionAssumptions,
) -> WorkloadDecision:
    """Compare whole projected rows with explicit workload requirements.

    A matching row must meet every known threshold for go. Unknown facts keep a
    possible pass at insufficient_data; if every row has a known failure, the
    result is no_go. All matching rows retain their evidence in the response.
    The selected row is representative, with workbook order breaking ties.
    """
    # Build list of requested target metrics
    supplied_targets: dict[MetricName, float | int] = {}
    if targets.min_throughput_tps is not None:
        supplied_targets["throughput"] = targets.min_throughput_tps
    if targets.min_generation_speed_tps_per_user is not None:
        supplied_targets["generation_speed"] = targets.min_generation_speed_tps_per_user
    if targets.max_ttft_ms is not None:
        supplied_targets["ttft"] = targets.max_ttft_ms
    if targets.min_context_window_tokens is not None:
        supplied_targets["context"] = targets.min_context_window_tokens
    if targets.max_cost_usd_per_million_tokens is not None:
        supplied_targets["cost"] = targets.max_cost_usd_per_million_tokens

    # Standard assumptions summary
    assumptions_summary: list[str] = [
        (
            "Projections are capacity estimates from normalized workbook sweeps "
            "and do not guarantee production SLA."
        )
    ]
    if assumptions.context_window_tokens is not None:
        assumptions_summary.append(
            f"Supported context window is a caller assumption of "
            f"{assumptions.context_window_tokens} tokens."
        )
    elif "context" in supplied_targets:
        assumptions_summary.append("Context window limit not supplied in assumptions.")

    if assumptions.hardware_cost_usd_per_box_hour is not None:
        assumptions_summary.append(
            "Hardware-only cost per million projected throughput tokens = "
            "box-hour price * 1,000,000 / (throughput_per_box * 3,600), "
            "assuming sustained projected capacity and excluding idle time and other costs. "
            f"Caller-supplied price: ${assumptions.hardware_cost_usd_per_box_hour:.2f}/box-hour."
        )
    elif "cost" in supplied_targets:
        assumptions_summary.append("Hardware box-hour cost not supplied in assumptions.")

    # Rule: If no customer limits/targets are supplied, return insufficient_data
    if not supplied_targets:
        return WorkloadDecision(
            status="insufficient_data",
            model_name=workbook.model_name,
            profile_id=workbook.profile_id,
            selected_record=None,
            selection_explanation=(
                "No decision thresholds were supplied; no configuration was selected."
            ),
            evidence=[],
            evaluated_configurations=[],
            unmet_constraints=[],
            unknown_constraints=[],
            assumptions=assumptions_summary,
        )

    # 1. Match requested scenario to workbook rows
    eligible_records: list[PerformanceRecord] = []
    for rec in workbook.records:
        match_input = targets.input_tokens is None or rec.input_length == targets.input_tokens
        match_output = targets.output_tokens is None or rec.output_length == targets.output_tokens
        match_cache = targets.cache_fraction is None or math.isclose(
            rec.cache_percentage, targets.cache_fraction, abs_tol=1e-5
        )
        if match_input and match_output and match_cache:
            eligible_records.append(rec)

    if not eligible_records:
        scenario_parts = [
            f"input={targets.input_tokens} tokens" if targets.input_tokens is not None else None,
            f"output={targets.output_tokens} tokens" if targets.output_tokens is not None else None,
            (
                f"cache fraction={targets.cache_fraction}"
                if targets.cache_fraction is not None
                else None
            ),
        ]
        requested_scenario = ", ".join(part for part in scenario_parts if part is not None)
        explanation = (
            f"No projected row matches {requested_scenario}."
            if requested_scenario
            else "The workbook contains no projected rows to evaluate."
        )
        units: dict[MetricName, str] = {
            "throughput": "t/s",
            "generation_speed": "t/s/user",
            "ttft": "ms",
            "context": "tokens",
            "cost": "USD/M projected throughput tokens",
        }
        return WorkloadDecision(
            status="insufficient_data",
            model_name=workbook.model_name,
            profile_id=workbook.profile_id,
            selected_record=None,
            selection_explanation=explanation,
            evidence=[
                ConstraintEvidence(
                    metric=metric,
                    outcome="unknown",
                    actual=None,
                    target=float(value),
                    unit=units[metric],
                    explanation=explanation,
                )
                for metric, value in supplied_targets.items()
            ],
            evaluated_configurations=[],
            unmet_constraints=[],
            unknown_constraints=list(supplied_targets.keys()),
            assumptions=assumptions_summary,
        )

    # 2 & 3 & 4. Evaluate each eligible record against supplied constraints
    evaluated_rows: list[EvaluatedRow] = []
    for rec in eligible_records:
        row_evidence: list[ConstraintEvidence] = []

        if "throughput" in supplied_targets:
            target_val = float(supplied_targets["throughput"])
            actual_val = rec.throughput
            met = actual_val >= target_val
            t_exp = (
                f"Projected throughput {actual_val:.2f} t/s >= target {target_val:.2f} t/s"
                if met
                else f"Projected throughput {actual_val:.2f} t/s < target {target_val:.2f} t/s"
            )
            row_evidence.append(
                ConstraintEvidence(
                    metric="throughput",
                    outcome="met" if met else "unmet",
                    actual=actual_val,
                    target=target_val,
                    unit="t/s",
                    explanation=t_exp,
                )
            )

        if "generation_speed" in supplied_targets:
            target_val = float(supplied_targets["generation_speed"])
            actual_val = rec.gen_speed
            met = actual_val >= target_val
            g_exp = (
                f"Projected gen speed {actual_val:.2f} t/s/user >= target {target_val:.2f} t/s/user"
                if met
                else f"Projected gen speed {actual_val:.2f} t/s/user "
                f"< target {target_val:.2f} t/s/user"
            )
            row_evidence.append(
                ConstraintEvidence(
                    metric="generation_speed",
                    outcome="met" if met else "unmet",
                    actual=actual_val,
                    target=target_val,
                    unit="t/s/user",
                    explanation=g_exp,
                )
            )

        if "ttft" in supplied_targets:
            target_val = float(supplied_targets["ttft"])
            actual_val = rec.ttft_ms
            met = actual_val <= target_val
            ttft_exp = (
                f"Projected TTFT {actual_val:.2f} ms <= target {target_val:.2f} ms"
                if met
                else f"Projected TTFT {actual_val:.2f} ms > target {target_val:.2f} ms"
            )
            row_evidence.append(
                ConstraintEvidence(
                    metric="ttft",
                    outcome="met" if met else "unmet",
                    actual=actual_val,
                    target=target_val,
                    unit="ms",
                    explanation=ttft_exp,
                )
            )

        if "context" in supplied_targets or assumptions.context_window_tokens is not None:
            scenario_tokens = rec.input_length + rec.output_length
            target_val = float(max(targets.min_context_window_tokens or 0, scenario_tokens))
            if assumptions.context_window_tokens is None:
                row_evidence.append(
                    ConstraintEvidence(
                        metric="context",
                        outcome="unknown",
                        actual=None,
                        target=target_val,
                        unit="tokens",
                        explanation=(
                            "Supported context window was not supplied; the projected scenario "
                            f"requires at least {scenario_tokens} input plus output tokens."
                        ),
                    )
                )
            else:
                actual_val = float(assumptions.context_window_tokens)
                met = actual_val >= target_val
                act_int, tgt_int = int(actual_val), int(target_val)
                ctx_exp = (
                    f"Assumed context window {act_int} tokens >= required {tgt_int} tokens "
                    f"({scenario_tokens} for this scenario)"
                    if met
                    else f"Assumed context window {act_int} tokens < required {tgt_int} tokens "
                    f"({scenario_tokens} for this scenario)"
                )
                row_evidence.append(
                    ConstraintEvidence(
                        metric="context",
                        outcome="met" if met else "unmet",
                        actual=actual_val,
                        target=target_val,
                        unit="tokens",
                        explanation=ctx_exp,
                    )
                )

        if "cost" in supplied_targets:
            target_val = float(supplied_targets["cost"])
            if assumptions.hardware_cost_usd_per_box_hour is None:
                row_evidence.append(
                    ConstraintEvidence(
                        metric="cost",
                        outcome="unknown",
                        actual=None,
                        target=target_val,
                        unit="USD/M projected throughput tokens",
                        explanation="hardware_cost_usd_per_box_hour assumption was not supplied",
                    )
                )
            elif rec.throughput_per_box <= 0:
                row_evidence.append(
                    ConstraintEvidence(
                        metric="cost",
                        outcome="unknown",
                        actual=None,
                        target=target_val,
                        unit="USD/M projected throughput tokens",
                        explanation=(
                            "Cost cannot be estimated because projected throughput_per_box "
                            "is not positive."
                        ),
                    )
                )
            else:
                # Formula: price_per_box_hour * 1_000_000 / (throughput_per_box * 3600)
                actual_val = (assumptions.hardware_cost_usd_per_box_hour * 1_000_000.0) / (
                    rec.throughput_per_box * 3600.0
                )
                met = actual_val <= target_val
                cost_exp = (
                    f"Hardware cost at projected capacity ${actual_val:.4f}/M tokens "
                    f"<= target ${target_val:.4f}/M tokens"
                    if met
                    else f"Hardware cost at projected capacity ${actual_val:.4f}/M tokens "
                    f"> target ${target_val:.4f}/M tokens"
                )
                row_evidence.append(
                    ConstraintEvidence(
                        metric="cost",
                        outcome="met" if met else "unmet",
                        actual=actual_val,
                        target=target_val,
                        unit="USD/M projected throughput tokens",
                        explanation=cost_exp,
                    )
                )

        unmet = [e.metric for e in row_evidence if e.outcome == "unmet"]
        unknown = [e.metric for e in row_evidence if e.outcome == "unknown"]
        evaluated_rows.append(
            {
                "record": rec,
                "evidence": row_evidence,
                "unmet": unmet,
                "unknown": unknown,
                "is_go": len(unmet) == 0 and len(unknown) == 0,
            }
        )

    evaluated_configurations = [
        ConfigurationEvaluation(
            record=row["record"],
            evidence=row["evidence"],
            unmet_constraints=row["unmet"],
            unknown_constraints=row["unknown"],
        )
        for row in evaluated_rows
    ]

    # 5 & 6. Determine overall decision status and select representative row
    go_rows = [r for r in evaluated_rows if r["is_go"]]
    if go_rows:
        selected = go_rows[0]
        return WorkloadDecision(
            status="go",
            model_name=workbook.model_name,
            profile_id=workbook.profile_id,
            selected_record=selected["record"],
            selection_explanation=(
                "First matching configuration meeting every check; ties follow workbook row order."
            ),
            evidence=selected["evidence"],
            evaluated_configurations=evaluated_configurations,
            unmet_constraints=[],
            unknown_constraints=[],
            assumptions=assumptions_summary,
        )

    # If no row passed all checks, check if any row failed purely due to UNKNOWN assumptions
    potential_go_rows = [r for r in evaluated_rows if len(r["unmet"]) == 0]
    if potential_go_rows:
        selected = potential_go_rows[0]
        return WorkloadDecision(
            status="insufficient_data",
            model_name=workbook.model_name,
            profile_id=workbook.profile_id,
            selected_record=selected["record"],
            selection_explanation=(
                "No confirmed pass; first configuration without a known failure is shown. "
                "Unknown checks could change the verdict."
            ),
            evidence=selected["evidence"],
            evaluated_configurations=evaluated_configurations,
            unmet_constraints=selected["unmet"],
            unknown_constraints=selected["unknown"],
            assumptions=assumptions_summary,
        )

    # Every eligible row failed at least one constraint
    selected = min(evaluated_rows, key=lambda r: len(r["unmet"]))
    return WorkloadDecision(
        status="no_go",
        model_name=workbook.model_name,
        profile_id=workbook.profile_id,
        selected_record=selected["record"],
        selection_explanation=(
            "Every matching configuration has a known failure. The row with the fewest "
            "failures is shown; ties follow workbook row order. See evaluated_configurations "
            "for the evidence from every row."
        ),
        evidence=selected["evidence"],
        evaluated_configurations=evaluated_configurations,
        unmet_constraints=selected["unmet"],
        unknown_constraints=selected["unknown"],
        assumptions=assumptions_summary,
    )
