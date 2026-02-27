import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'vesUI',
      filename: 'remoteEntry.js',
      exposes: { './VesModule': './src/VesModule.tsx' },
      remotes: { shell: 'http://shell-ui/assets/remoteEntry.js' },
      shared: {
        react:       { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
  build: { target: 'esnext', modulePreload: false, minify: false, cssCodeSplit: false },
  server: {
    port: 5011,
    proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true } },
  },
});
