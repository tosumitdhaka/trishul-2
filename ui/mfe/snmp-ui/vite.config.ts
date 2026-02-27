import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'snmpUI',
      filename: 'remoteEntry.js',
      exposes: { './SnmpModule': './src/SnmpModule.tsx' },
      shared: {
        react:       { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
  // es2015 target makes vite-plugin-federation emit IIFE-style remoteEntry.js
  // which registers window[name] synchronously — required for dynamic script loading.
  // esnext emits ESM exports instead and window[name] is never set.
  build: { target: 'es2015', modulePreload: false, minify: false, cssCodeSplit: false },
  server: {
    port: 5010,
    proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true }, '/ws': { target: 'http://core-api:8000', ws: true, changeOrigin: true } },
  },
});
