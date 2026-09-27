import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    ...devices['Desktop Chrome'],
  },
  webServer: [
    {
      command:
        '".venv\\Scripts\\python.exe" -m uvicorn perf_api.main:app --host 127.0.0.1 --port 8017',
      cwd: '../backend',
      url: 'http://127.0.0.1:8017/health',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run dev -- --port 4173 --strictPort',
      env: { VITE_DEV_API_TARGET: 'http://127.0.0.1:8017' },
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
