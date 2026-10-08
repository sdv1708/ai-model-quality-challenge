import { defineConfig } from '@playwright/test'
import base from './playwright.config'

// Start vercel dev --local, or set PLAYWRIGHT_BASE_URL to a deployed origin.
export default defineConfig({
  ...base,
  use: { ...base.use, baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000' },
  webServer: [],
})
