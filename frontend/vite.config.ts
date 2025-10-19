import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/ws': {
        target: 'http://localhost:8000',  // Changed from ws:// to http://
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path,
        // Add timeout and error handling for WebSocket connections
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[vite] WebSocket proxy error:', err.message);
          });
          proxy.on('proxyReqWs', (proxyReq, req, socket) => {
            socket.on('error', (err) => {
              console.error('[vite] WebSocket proxy socket error:', err.message);
            });
          });
          proxy.on('open', (proxySocket) => {
            console.log('[vite] WebSocket proxy connection opened');
            proxySocket.on('error', (err) => {
              console.error('[vite] WebSocket proxy backend socket error:', err.message);
            });
          });
        }
      }
    }
  }
});
