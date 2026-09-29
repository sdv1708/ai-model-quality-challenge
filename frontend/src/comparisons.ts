import type { NormalizedWorkbook, PerformanceRecord } from './workbooks'

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

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function errorDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null
  const detail = body.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return null
        if ('message' in item && typeof item.message === 'string') {
          const filename =
            'filename' in item && typeof item.filename === 'string' ? item.filename : ''
          return filename ? `${filename}: ${item.message}` : item.message
        }
        return 'msg' in item && typeof item.msg === 'string' ? item.msg : null
      })
      .filter((message): message is string => message !== null)
    return messages.length ? messages.join('; ') : null
  }
  return null
}

export async function compareWorkbooks(files: File[]): Promise<ComparisonResponse> {
  if (files.length === 0) throw new Error('Choose at least one Excel workbook.')

  const form = new FormData()
  for (const file of files) form.append('workbooks', file)

  let response: Response
  try {
    response = await fetch(`${apiBase}/api/v1/comparisons/workbooks`, {
      method: 'POST',
      body: form,
    })
  } catch {
    throw new Error('Could not reach the comparison API. Check that the backend is running.')
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    throw new Error(
      errorDetail(body) ?? `The workbooks could not be processed (HTTP ${response.status}).`,
    )
  }

  const result = (await response.json()) as ComparisonResponse
  if (result.workbooks.length === 0) {
    throw new Error(
      result.diagnostics.map((diagnostic) => diagnostic.message).join(' ') ||
        'No usable workbooks were returned.',
    )
  }
  return result
}
