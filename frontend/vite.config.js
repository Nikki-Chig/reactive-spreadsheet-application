import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => {
  // Load environment variables based on the mode (development, production, etc.)
  const env = loadEnv(mode, process.cwd());

  return {
    plugins: [svelte()],
    build: {
      outDir: 'dist',
    },
    server: {
      proxy: {
        '/api': env.VITE_WEBSOCKET_URL || 'http://localhost:8888', // Use the loaded environment variable
      },
    },
  };
});
