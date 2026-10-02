import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo, /api se redirige al backend FastAPI (puerto 8001; se cambia con BACKEND_URL).
    proxy: {
      '/api': process.env.BACKEND_URL ?? 'http://localhost:8001',
    },
  },
})
