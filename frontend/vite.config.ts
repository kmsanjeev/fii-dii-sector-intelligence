import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,           // bind 0.0.0.0 so Cloudflare Tunnel can reach it
    allowedHosts: 'all',  // allow any hostname (tunnel gives *.trycloudflare.com)
    proxy: {
      '/api': 'http://localhost:8001',
      '/ws':  { target: 'ws://localhost:8001', ws: true },
    },
  },
})
