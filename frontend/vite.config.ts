/// <reference types="vitest/config" />
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Proxy /api -> backend local (RF-F0-13). En producción se usa VITE_API_URL (RF-F0-18).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
    // Permite leer ../replays/*.json (los replays se empaquetan en el build, RF-F3-46).
    fs: { allow: ['..'] },
  },
  test: {
    environment: 'node',
  },
})
