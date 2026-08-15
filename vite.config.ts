import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {fileURLToPath} from 'url';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  const apiTarget = process.env.SENTINEL_PROXY_TARGET || 'http://localhost:5000';
  const rootDir = path.dirname(fileURLToPath(import.meta.url));
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(rootDir, '.'),
      },
    },
    server: {
      proxy: {
        '/api': apiTarget
      },
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // File watching can be disabled in hosted edit sessions to prevent flicker.
      hmr: process.env.DISABLE_HMR !== 'true',
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            charts: ['recharts', 'd3-array', 'd3-scale', 'd3-shape'],
            motion: ['motion'],
          },
        },
      },
    },
  };
});
