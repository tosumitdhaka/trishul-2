import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'shell',
      // remotes are loaded DYNAMICALLY at runtime from /api/v1/plugins/registry
      // static remotes can be added here during Phase 5:
      // remotes: { snmpUI: 'http://snmp-ui:5001/assets/remoteEntry.js' },
      remotes: {},
      shared: {
        react:     { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
        zustand:   { singleton: true },
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
