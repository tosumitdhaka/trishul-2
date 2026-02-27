import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

const MFE_TARGET = ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'];

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'logViewer',
      filename: 'remoteEntry.js',
      exposes: { './LogViewerModule': './src/LogViewerModule.tsx' },
      shared: {
        react:       { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
  build: { target: MFE_TARGET, modulePreload: false, minify: false, cssCodeSplit: false },
  server: {
    port: 5022,
    proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true }, '/ws': { target: 'http://core-api:8000', ws: true, changeOrigin: true } },
  },
});
