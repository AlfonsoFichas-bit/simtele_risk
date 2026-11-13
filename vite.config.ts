import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig(({ command }) => ({
  // In production the bundle is served from Django's STATIC_URL. In
  // development the entry is loaded directly from the Vite dev server, so the
  // base must stay at "/" for that URL to resolve.
  base: command === 'build' ? '/static/build/' : '/',
  plugins: [vue(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'static/build',
    emptyOutDir: true,
    manifest: 'manifest.json',
    rollupOptions: {
      input: 'frontend/main.ts',
    },
  },
}))
