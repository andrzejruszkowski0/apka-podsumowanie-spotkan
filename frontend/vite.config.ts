import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/people': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/topics': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/meetings': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
