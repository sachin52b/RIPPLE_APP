import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Temporary Cloudflare Quick Tunnel hostname used for the live prototype demo.
    allowedHosts: ['campus-basis-buzz-indicator.trycloudflare.com'],
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
