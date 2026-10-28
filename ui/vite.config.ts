import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // FastAPI backend (licensewise/api.py); same-origin in the browser, so no CORS setup
  server: { proxy: { "/api": "http://localhost:8000" } },
})
