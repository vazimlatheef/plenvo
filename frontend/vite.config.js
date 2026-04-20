import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '^/auth': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '^/me': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '^/users': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '^/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
