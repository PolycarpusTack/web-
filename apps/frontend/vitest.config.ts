import { defineConfig } from 'vitest/config';
import { resolve } from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test-utils/setup.ts'],
    include: [
      'src/**/*.{test,spec}.{ts,tsx}',
      'src/**/__tests__/**/*.{ts,tsx}',
    ],
    exclude: [
      'node_modules',
      'dist',
      'build',
      'coverage',
      'src/main.tsx',
      'src/vite-env.d.ts',
      '**/*.config.*',
      '**/e2e/**',
    ],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@/components': resolve(__dirname, 'src/components'),
      '@/lib': resolve(__dirname, 'src/lib'),
      '@/hooks': resolve(__dirname, 'src/hooks'),
      '@/api': resolve(__dirname, 'src/api'),
      '@/pages': resolve(__dirname, 'src/pages'),
      '@/types': resolve(__dirname, 'src/types'),
      '@/config': resolve(__dirname, 'src/config'),
      '@/test-utils': resolve(__dirname, 'src/test-utils'),
    },
  },
});