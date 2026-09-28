export interface PerformanceRecord {
  input_length: number
  output_length: number
  cache_percentage: number
  batch_size: number
  max_ms: number
  target_max_ms: number
  prompt_throughput: number
  gen_throughput: number
  throughput: number
  throughput_per_box: number
  uncached_throughput: number
  uncached_throughput_per_box: number
  cached_throughput: number
  cached_throughput_per_box: number
  ttft_ms: number
  real_prompt_speed: number
  prompt_speed_queued: number
  gen_speed: number
  rpm: number
}

export interface NormalizedWorkbook {
  model_name: string
  profile_id: string
  record_count: number
  records: PerformanceRecord[]
}

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function normalizeWorkbook(file: File): Promise<NormalizedWorkbook> {
  const form = new FormData()
  form.append('workbook', file)

  let response: Response
  try {
    response = await fetch(`${apiBase}/api/v1/workbooks/normalize`, {
      method: 'POST',
      body: form,
    })
  } catch {
    throw new Error(
      'Could not reach the workbook API. Check that the backend is running and try again.',
    )
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    const detail = error?.detail
    throw new Error(
      typeof detail === 'string'
        ? detail
        : `The workbook could not be processed (HTTP ${response.status}).`,
    )
  }

  return response.json() as Promise<NormalizedWorkbook>
}

export async function loadSampleWorkbook(): Promise<File> {
  const response = await fetch('/sample/Model%20A%20profile%201.xlsx')
  if (!response.ok) {
    throw new Error('The sample workbook is unavailable. Try uploading a local .xlsx file.')
  }
  const blob = await response.blob()
  return new File([blob], 'Model A profile 1.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
}
