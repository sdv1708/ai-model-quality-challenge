import type { NormalizedWorkbook, PerformanceRecord } from './workbooks'

export interface SourceReference {
  model_name: string
  profile_id: string
  workbook_index: number
  record_index: number
  filename: string | null
  worksheet: string | null
  sheet_row: number | null
}

export interface EngineeringMetric {
  name: string
  value: number
  unit: string
  explanation: string
}

export interface ConfigurationDiagnostic {
  source: SourceReference
  record: PerformanceRecord
  metrics: EngineeringMetric[]
}

export interface TrendDiagnostic {
  dimension: 'batch_size' | 'cache_percentage' | 'configuration'
  baseline: SourceReference
  candidate: SourceReference
  metric_name: string
  baseline_value: number
  candidate_value: number
  unit: string
  explanation: string
}

export interface AnomalyFlag {
  code: string
  rule: string
  explanation: string
  sources: SourceReference[]
}

export interface EngineeringAnalysisResponse {
  configurations: ConfigurationDiagnostic[]
  trends: TrendDiagnostic[]
  anomalies: AnomalyFlag[]
  limitations: string[]
}

export async function analyzeEngineering(
  workbooks: NormalizedWorkbook[],
  signal?: AbortSignal,
): Promise<EngineeringAnalysisResponse> {
  let response: Response
  try {
    response = await fetch('/api/v1/engineering/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workbooks }),
      signal,
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new Error('Could not reach the engineering API. Check that the backend is running.')
  }

  if (!response.ok) {
    throw new Error(`Engineering analysis could not be loaded (HTTP ${response.status}).`)
  }
  return response.json() as Promise<EngineeringAnalysisResponse>
}
