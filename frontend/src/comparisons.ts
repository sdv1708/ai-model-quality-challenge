import type { NormalizedWorkbook, PerformanceRecord } from './workbooks'

// TODO(issue #6, step 7): Keep these shapes in sync with the final backend
// OpenAPI response. Revisit them if the learner changes the alignment policy.
export interface ConfigurationKey {
  profile_id: string
  input_length: number
  output_length: number
  cache_percentage: number
  batch_size: number
}

export interface AlignedConfiguration {
  key: ConfigurationKey
  members: { model_name: string; record: PerformanceRecord }[]
  missing_models: string[]
  is_comparable: boolean
}

export interface ComparisonDiagnostic {
  code: string
  message: string
  filename: string | null
  model_name: string | null
  profile_id: string | null
}

export interface ComparisonResponse {
  workbooks: NormalizedWorkbook[]
  models: string[]
  configurations: AlignedConfiguration[]
  diagnostics: ComparisonDiagnostic[]
}

export async function compareWorkbooks(_files: File[]): Promise<ComparisonResponse> {
  // TODO(issue #6, step 7): Send every File under the repeated `workbooks`
  // multipart field, parse per-file errors, and surface comparison coverage.
  throw new Error('Issue #6 multi-workbook upload is not implemented yet.')
}
