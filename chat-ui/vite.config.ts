import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/rag': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/ai': 'http://localhost:8000',
    }
  }
})
