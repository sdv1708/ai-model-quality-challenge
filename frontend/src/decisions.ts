import type { NormalizedWorkbook, PerformanceRecord } from './workbooks'

export type MetricName = 'throughput' | 'generation_speed' | 'ttft' | 'context' | 'cost'
export type DecisionStatus = 'go' | 'no_go' | 'insufficient_data'
export type EvidenceOutcome = 'met' | 'unmet' | 'unknown'

export interface WorkloadTargets {
  input_tokens?: number
  output_tokens?: number
  cache_fraction?: number
  min_throughput_tps?: number
  min_generation_speed_tps_per_user?: number
  max_ttft_ms?: number
  min_context_window_tokens?: number
  max_cost_usd_per_million_tokens?: number
}

export interface DecisionAssumptions {
  context_window_tokens?: number
  hardware_cost_usd_per_box_hour?: number
}

export interface ConstraintEvidence {
  metric: MetricName
  outcome: EvidenceOutcome
  actual: number | null
  target: number | null
  unit: string
  explanation: string
}

export interface ConfigurationEvaluation {
  record: PerformanceRecord
  evidence: ConstraintEvidence[]
  unmet_constraints: MetricName[]
  unknown_constraints: MetricName[]
}

export interface WorkloadDecision {
  status: DecisionStatus
  model_name: string
  profile_id: string
  selected_record: PerformanceRecord | null
  selection_explanation: string
  evidence: ConstraintEvidence[]
  evaluated_configurations: ConfigurationEvaluation[]
  unmet_constraints: MetricName[]
  unknown_constraints: MetricName[]
  assumptions: string[]
}

export async function evaluateDecision(
  workbook: NormalizedWorkbook,
  targets: WorkloadTargets,
  assumptions: DecisionAssumptions,
): Promise<WorkloadDecision> {
  let response: Response
  try {
    response = await fetch('/api/v1/decisions/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workbook, targets, assumptions }),
    })
  } catch {
    throw new Error(
      'Could not reach the decision API. Check that the backend is running and try again.',
    )
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `The workload could not be evaluated (HTTP ${response.status}).`,
    )
  }

  return response.json() as Promise<WorkloadDecision>
}
