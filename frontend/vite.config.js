import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/copilotkit': { target: 'http://backend:8000', changeOrigin: true },
      '/api':        { target: 'http://backend:8000', changeOrigin: true,
                       rewrite: p => p.replace(/^\/api/, '') },
    },
  },
})
