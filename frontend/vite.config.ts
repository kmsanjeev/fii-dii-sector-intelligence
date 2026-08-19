import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,           // bind 0.0.0.0 so Cloudflare Tunnel can reach it
    allowedHosts: true,   // allow any hostname (tunnel gives *.trycloudflare.com)
    proxy: {
      '/api': 'http://localhost:8001',
      '/ws':  { target: 'ws://localhost:8001', ws: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    include: ['src/test/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['**/node_modules/**', '**/node_modules.*/*', '**/.git/**'],
  },
})
