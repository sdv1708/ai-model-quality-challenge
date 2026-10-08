import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000',
    },
  },
  // Standalone local verification uses this proxy. Vercel routes /api directly
  // to the backend service through the root vercel.json in dev and production.
  preview: {
    proxy: {
      '/api': process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000',
    },
  },
})
