/**
 * Custom render utilities for testing React components
 * Provides wrappers with all necessary providers and context
 */

import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

// ==========================================
// PROVIDERS AND CONTEXT SETUP
// ==========================================

// Mock AuthProvider component (avoids circular dependency issues)
const MockAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

// Mock ThemeProvider component
const MockThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <div data-theme="light">{children}</div>;
};

// Mock ToastProvider for sonner/toast notifications
const MockToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <div data-testid="toast-provider">
      {children}
      <div id="toast-container" />
    </div>
  );
};

// ==========================================
// CUSTOM RENDER FUNCTIONS
// ==========================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Router options
  initialEntries?: string[];
  route?: string;
  
  // Provider options
  withRouter?: boolean;
  withAuth?: boolean;
  withTheme?: boolean;
  withToast?: boolean;
  
  // Custom wrapper
  wrapper?: React.ComponentType<{ children: ReactNode }>;
}

/**
 * Default providers wrapper
 */
const DefaultProvidersWrapper: React.FC<{ 
  children: ReactNode;
  options: CustomRenderOptions;
}> = ({ children, options }) => {
  const {
    withRouter = true,
    withAuth = true,
    withTheme = true,
    withToast = true,
    initialEntries = ['/'],
    route = '/',
  } = options;

  let wrapped = children;

  // Wrap with auth provider if needed
  if (withAuth) {
    wrapped = <MockAuthProvider>{wrapped}</MockAuthProvider>;
  }

  // Wrap with theme provider if needed
  if (withTheme) {
    wrapped = <MockThemeProvider>{wrapped}</MockThemeProvider>;
  }

  // Wrap with toast provider if needed
  if (withToast) {
    wrapped = <MockToastProvider>{wrapped}</MockToastProvider>;
  }

  // Wrap with router if needed
  if (withRouter) {
    if (initialEntries.length > 1 || route !== '/') {
      wrapped = (
        <MemoryRouter initialEntries={initialEntries} initialIndex={0}>
          {wrapped}
        </MemoryRouter>
      );
    } else {
      wrapped = <BrowserRouter>{wrapped}</BrowserRouter>;
    }
  }

  return <>{wrapped}</>;
};

/**
 * Custom render function with all providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult {
  const { wrapper, ...renderOptions } = options;

  const Wrapper = wrapper || (({ children }: { children: ReactNode }) => (
    <DefaultProvidersWrapper options={options}>
      {children}
    </DefaultProvidersWrapper>
  ));

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

/**
 * Render component with router only (useful for testing routing components)
 */
export function renderWithRouter(
  ui: ReactElement,
  options: {
    initialEntries?: string[];
    initialIndex?: number;
  } & Omit<RenderOptions, 'wrapper'> = {}
): RenderResult {
  const { initialEntries = ['/'], initialIndex = 0, ...renderOptions } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
        {children}
      </MemoryRouter>
    ),
    ...renderOptions,
  });
}

/**
 * Render component without any providers (for isolated testing)
 */
export function renderWithoutProviders(
  ui: ReactElement,
  options: RenderOptions = {}
): RenderResult {
  return render(ui, options);
}

// ==========================================
// MOCK UTILITIES
// ==========================================

/**
 * Create mock API response
 */
export function createMockApiResponse<T>(
  data: T,
  success = true,
  error?: string
) {
  return {
    success,
    data: success ? data : undefined,
    error: success ? undefined : (error || 'Mock error'),
  };
}

/**
 * Create mock API function that returns a response
 */
export function createMockApiFunction<T>(
  response: T,
  delay = 0
) {
  return vi.fn().mockImplementation(() => {
    if (delay > 0) {
      return new Promise(resolve => setTimeout(() => resolve(response), delay));
    }
    return Promise.resolve(response);
  });
}

/**
 * Mock user for authentication tests
 */
export const mockUser = {
  id: 'test-user-1',
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_superuser: false,
};

/**
 * Mock conversation for chat tests
 */
export const mockConversation = {
  id: 'test-conversation-1',
  title: 'Test Conversation',
  model_id: 'gpt-3.5-turbo',
  created_at: '2024-01-01T00:00:00.000Z',
  updated_at: '2024-01-01T00:00:00.000Z',
  user_id: 'test-user-1',
  message_count: 2,
  messages: [
    {
      id: 'test-message-1',
      role: 'user' as const,
      content: 'Hello, world!',
      created_at: '2024-01-01T00:00:00.000Z',
      tokens: 10,
    },
    {
      id: 'test-message-2',
      role: 'assistant' as const,
      content: 'Hello! How can I help you today?',
      created_at: '2024-01-01T00:00:05.000Z',
      tokens: 15,
    },
  ],
};

/**
 * Mock file for file upload tests
 */
export const mockFile = new File(['test content'], 'test.txt', {
  type: 'text/plain',
});

/**
 * Mock auth context values
 */
export const mockAuthContext = {
  user: mockUser,
  tokens: {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_at: '2024-12-31T23:59:59.000Z',
  },
  isAuthenticated: true,
  isLoading: false,
  error: null,
  login: vi.fn().mockResolvedValue(true),
  logout: vi.fn(),
  refreshTokens: vi.fn().mockResolvedValue(true),
  clearError: vi.fn(),
};

// ==========================================
// UTILITIES FOR ASYNC TESTING
// ==========================================

/**
 * Wait for the next tick (useful for async operations)
 */
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

/**
 * Wait for a specific amount of time
 */
export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Wait for an element to appear (alternative to waitFor from testing-library)
 */
export const waitForElement = async (
  callback: () => HTMLElement | null,
  timeout = 1000
): Promise<HTMLElement> => {
  const start = Date.now();
  
  while (Date.now() - start < timeout) {
    const element = callback();
    if (element) {
      return element;
    }
    await waitForNextTick();
  }
  
  throw new Error(`Element not found within ${timeout}ms`);
};

// ==========================================
// EXPORTS
// ==========================================

// Re-export everything from testing-library
export * from '@testing-library/react';
export * from '@testing-library/user-event';

// Override the default render with our custom one
export { renderWithProviders as render };