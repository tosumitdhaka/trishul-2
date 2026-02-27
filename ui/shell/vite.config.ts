import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'shell',
      remotes: {},  // Phase 5 remotes loaded dynamically at runtime via RemotePage
      // Expose shared design system so MFE remotes can import it
      exposes: {
        './design-system': './src/design-system/index.ts',
      },
      shared: {
        react:     { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
        zustand:   { singleton: true },
        axios:     { singleton: true },
      },
    }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  build: {
    target:         'esnext',
    modulePreload:  false,
    minify:         false,
    cssCodeSplit:   false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api':    { target: 'http://core-api:8000', changeOrigin: true },
      '/health': { target: 'http://core-api:8000', changeOrigin: true },
      '/ws':     { target: 'ws://core-api:8000',   ws: true, changeOrigin: true },
    },
  },
});
