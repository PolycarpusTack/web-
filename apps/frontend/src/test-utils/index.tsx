/**
 * Test utilities for Vitest and React Testing Library
 * Provides custom render function with providers and common test helpers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth-context';
import { ThemeProvider } from '@/lib/theme-provider';
import { vi } from 'vitest';

// Mock auth context for tests
vi.mock('@/lib/auth-context', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    tokens: null,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshTokens: vi.fn(),
    clearError: vi.fn(),
    isLoading: false,
    isAuthenticated: false,
    error: null,
  }),
}));

// Custom render function that includes providers
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Helper to create mock API responses
export const createMockApiResponse = <T,>(data: T, success = true) => ({
  success,
  data: success ? data : undefined,
  error: success ? undefined : 'Mock error',
});

// Helper to wait for async operations
export const waitForAsync = async (ms = 0) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Mock navigation function
export const mockNavigate = vi.fn();

// Helper to mock window.location
export const mockWindowLocation = (pathname: string) => {
  Object.defineProperty(window, 'location', {
    value: {
      pathname,
      search: '',
      hash: '',
      href: `http://localhost:3000${pathname}`,
    },
    writable: true,
  });
};