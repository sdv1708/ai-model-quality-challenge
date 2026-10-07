import { defineConfig } from '@playwright/test'
import base from './playwright.config'
import { backendCommand } from './tests/support/runtime'

// preview:e2e builds first with the managed local API configuration.
// Vite preview is a local verification server, not the public production host.
export default defineConfig({
  ...base,
  use: { ...base.use, baseURL: 'http://127.0.0.1:4174' },
  webServer: [
    {
      command: backendCommand(8018),
      cwd: '../backend',
      url: 'http://127.0.0.1:8018/health',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run preview:e2e -- --port 4174 --strictPort',
      env: { VITE_DEV_API_TARGET: 'http://127.0.0.1:8018', VITE_API_BASE_URL: '' },
      url: 'http://127.0.0.1:4174',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
