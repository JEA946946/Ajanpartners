import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Split heavy, stable vendor libs into independently-cached chunks
        // (Recharts alone was ~380 KB folded into the Dashboard route).
        manualChunks: {
          'vendor-mui': ['@mui/material', '@mui/x-date-pickers'],
          'vendor-recharts': ['recharts'],
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        // Lokalt kan API'et køre på en anden port (fx når 8001 er optaget): BOOKKEEPING_API_URL.
        target: process.env.BOOKKEEPING_API_URL ?? 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
});
