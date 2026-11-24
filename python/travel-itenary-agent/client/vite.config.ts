/// <reference types="vitest/config" />
import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Forward API calls to the Python agent so the browser sees one origin.
    proxy: {'/api': 'http://127.0.0.1:8000'},
  },
  test: {
    environment: 'jsdom',
  },
});
