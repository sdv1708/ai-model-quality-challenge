import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000',
    },
  },
  // Issue #10: exercise the built bundle through a local same-origin API proxy.
  // Public hosting and separately hosted API/CORS verification belong to issue #11.
  preview: {
    proxy: {
      '/api': process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000',
    },
  },
})
