import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'sftpAvroUI',
      filename: 'remoteEntry.js',
      exposes: {
        './SftpModule': './src/SftpModule.tsx',
        './AvroModule': './src/AvroModule.tsx',
      },
      remotes: { shell: 'http://shell-ui/assets/remoteEntry.js' },
      shared: { react: { singleton: true }, 'react-dom': { singleton: true } },
    }),
  ],
  build: { target: 'esnext', modulePreload: false, minify: false, cssCodeSplit: false },
  server: { port: 5014, proxy: { '/api': { target: 'http://core-api:8000', changeOrigin: true } } },
});
