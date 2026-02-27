import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

// Target rationale: @originjs/vite-plugin-federation generates top-level await
// in shared-module glue (importShared). These browser versions all support TLA
// AND the plugin still emits an IIFE that registers window[name] synchronously.
// - 'esnext' breaks: emits ESM exports, window[name] never set
// - 'es2015' breaks: esbuild rejects top-level await at that target
const MFE_TARGET = ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'];

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
  build: { target: MFE_TARGET, modulePreload: false, minify: false, cssCodeSplit: false },
  server: {
    port: 5010,
    proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true }, '/ws': { target: 'http://core-api:8000', ws: true, changeOrigin: true } },
  },
});
