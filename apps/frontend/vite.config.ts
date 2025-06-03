/// <reference types="vitest" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
        "@/components": resolve(__dirname, "src/components"),
        "@/lib": resolve(__dirname, "src/lib"),
        "@/hooks": resolve(__dirname, "src/hooks"),
        "@/api": resolve(__dirname, "src/api"),
        "@/pages": resolve(__dirname, "src/pages"),
        "@/types": resolve(__dirname, "src/types"),
        "@/config": resolve(__dirname, "src/config"),
        "@/test-utils": resolve(__dirname, "src/test-utils"),
      },
    },
    server: {
      port: 5173,
      proxy: mode === 'development' ? {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true,
        },
      } : undefined,
    },
    build: {
      sourcemap: mode === 'development',
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-tabs'],
          },
        },
      },
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom'],
      esbuildOptions: {
        sourcemap: mode === 'development',
      },
    },
    
    // =========================================
    // COMPREHENSIVE VITEST CONFIGURATION
    // =========================================
    test: {
      // Global test settings
      globals: true,
      environment: 'happy-dom', // Faster than jsdom for most React testing
      
      // Setup files that run before each test
      setupFiles: ['./src/test-utils/setup.ts'],
      
      // Include/exclude patterns
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
      
      // Test timeout settings
      testTimeout: 10000,
      hookTimeout: 10000,
      
      // File watching
      watchExclude: [
        'node_modules',
        'dist',
        'build',
        'coverage',
      ],
      
      // Coverage configuration
      coverage: {
        provider: 'v8',
        reporter: [
          'text',      // Console output
          'text-summary',
          'json',      // For CI/CD integration
          'json-summary',
          'html',      // Human-readable reports
          'lcov',      // For external tools
        ],
        
        // Coverage thresholds - enforce quality
        thresholds: {
          global: {
            branches: 70,
            functions: 75,
            lines: 80,
            statements: 80,
          },
          // Per-file thresholds for critical files
          'src/lib/auth-context.tsx': {
            branches: 80,
            functions: 90,
            lines: 85,
            statements: 85,
          },
          'src/components/ui/**': {
            branches: 75,
            functions: 80,
            lines: 85,
            statements: 85,
          },
        },
        
        // What to include/exclude in coverage
        include: [
          'src/**/*.{ts,tsx}',
        ],
        exclude: [
          'src/main.tsx',
          'src/vite-env.d.ts',
          'src/**/*.d.ts',
          'src/test-utils/**',
          'src/**/__tests__/**',
          'src/**/*.test.{ts,tsx}',
          'src/**/*.spec.{ts,tsx}',
          'src/**/index.{ts,tsx}',
          'src/types/**',
          'src/config/**',
          'src/registry/**',
          '**/*.stories.{ts,tsx}',
          '**/node_modules/**',
        ],
        
        // Coverage output
        reportsDirectory: './coverage',
        
        // Enforce coverage in CI
        skipFull: false,
        all: true,
      },
      
      // Reporters
      reporters: [
        'default',
        'verbose',
        'json',
        'junit',
      ],
      outputFile: {
        json: './test-results/vitest-results.json',
        junit: './test-results/vitest-results.xml',
      },
      
      // Pool settings for performance
      pool: 'threads',
      poolOptions: {
        threads: {
          minThreads: 1,
          maxThreads: 4,
        },
      },
      
      // Mock settings
      clearMocks: true,
      restoreMocks: true,
      mockReset: true,
      
      // Error handling
      passWithNoTests: false,
      allowOnly: process.env.NODE_ENV !== 'production',
      
      // UI settings (for vitest --ui)
      ui: false,
      open: false,
      
      // Experimental features
      typecheck: {
        enabled: false, // Disable for now as it's experimental
        tsconfig: './tsconfig.json',
      },
    },
  };
});