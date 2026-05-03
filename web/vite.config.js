import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Root is web/ — Vite serves from here in dev mode
  root: '.',

  build: {
    outDir: 'dist',
    emptyOutDir: true,

    rollupOptions: {
      input: {
        // SPA pages only — tools are developer-only and served raw
        main: resolve(__dirname, 'index.html'),
        dsgvo: resolve(__dirname, 'dsgvo.html'),
      },
    },

    // Increase chunk-size warning threshold (large game config bundles expected)
    chunkSizeWarningLimit: 1000,
  },

  // In dev mode, proxy API/WS requests to the game server
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/ws':  { target: 'ws://localhost:8080',  ws: true, changeOrigin: true },
    },
  },
});
