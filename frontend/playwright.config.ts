import { defineConfig, devices } from '@playwright/test'
import { backendCommand } from './tests/support/runtime'

export default defineConfig({
  testDir: './tests',
  globalSetup: './tests/support/global-setup.ts',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    ...devices['Desktop Chrome'],
  },
  webServer: [
    {
      command: backendCommand(8017),
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
