import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'pmDashboard',
      filename: 'remoteEntry.js',
      exposes: { './PmDashboardModule': './src/PmDashboardModule.tsx' },
      shared: {
        react:       { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
  build: { target: 'es2015', modulePreload: false, minify: false, cssCodeSplit: false },
  server: {
    port: 5021,
    proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true }, '/ws': { target: 'http://core-api:8000', ws: true, changeOrigin: true } },
  },
});
