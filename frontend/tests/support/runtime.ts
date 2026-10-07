import path from 'node:path'

export const backendDirectory = path.resolve(import.meta.dirname, '../../../backend')
export const backendPython = path.join(
  backendDirectory,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
)

// Quote absolute paths because Windows user/workspace directories can contain spaces.
export function backendCommand(port: number) {
  return `"${backendPython}" -m uvicorn perf_api.main:app --host 127.0.0.1 --port ${port}`
}
