/**
 * Global test setup file for Vitest
 * This file runs before each test and sets up the testing environment
 */

import { cleanup } from '@testing-library/react';
import { afterEach, vi, beforeAll, afterAll, expect } from 'vitest';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// ==========================================
// CLEANUP AND LIFECYCLE HOOKS
// ==========================================

// Cleanup after each test to prevent memory leaks
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.clearAllTimers();
});

beforeAll(() => {
  // Global setup that runs once before all tests
  vi.useFakeTimers();
});

afterAll(() => {
  // Global cleanup that runs once after all tests
  vi.useRealTimers();
});

// ==========================================
// DOM API MOCKS (Only if DOM is available)
// ==========================================

if (typeof window !== 'undefined') {
  // Mock window.matchMedia (used by many UI components)
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // deprecated
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Mock localStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    key: vi.fn(),
    length: 0,
  };
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true,
  });

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    key: vi.fn(),
    length: 0,
  };
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock,
    writable: true,
  });

  // Mock window.location
  const mockLocation = {
    href: 'http://localhost:3000/',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
    assign: vi.fn(),
    replace: vi.fn(),
    reload: vi.fn(),
  };

  Object.defineProperty(window, 'location', {
    value: mockLocation,
    writable: true,
  });

  // Mock window.navigate (if using programmatic navigation)
  Object.defineProperty(window, 'navigate', {
    value: vi.fn(),
    writable: true,
  });
}

// ==========================================
// GLOBAL API MOCKS
// ==========================================

// Mock ResizeObserver (used by many modern UI components)
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
global.ResizeObserver = MockResizeObserver as any;

// Mock IntersectionObserver (used for lazy loading, etc.)
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  
  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    // Store callback and options if needed for testing
  }
}
global.IntersectionObserver = MockIntersectionObserver as any;

// Mock fetch globally
global.fetch = vi.fn();

// Mock URL.createObjectURL and URL.revokeObjectURL (for file handling)
global.URL.createObjectURL = vi.fn(() => 'mock-object-url');
global.URL.revokeObjectURL = vi.fn();

if (typeof Element !== 'undefined') {
  // Mock scrollIntoView (commonly used in UI components)
  Element.prototype.scrollIntoView = vi.fn();
}

if (typeof HTMLCanvasElement !== 'undefined') {
  // Mock HTMLCanvasElement.getContext (for chart libraries, etc.)
  HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi.fn(() => ({ data: new Array(4) })),
    putImageData: vi.fn(),
    createImageData: vi.fn(() => []),
    setTransform: vi.fn(),
    drawImage: vi.fn(),
    save: vi.fn(),
    fillText: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    translate: vi.fn(),
    scale: vi.fn(),
    rotate: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    measureText: vi.fn(() => ({ width: 0 })),
    transform: vi.fn(),
    rect: vi.fn(),
    clip: vi.fn(),
  });
}

if (typeof navigator !== 'undefined') {
  // Mock clipboard API
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: vi.fn().mockResolvedValue(undefined),
      readText: vi.fn().mockResolvedValue(''),
    },
    writable: true,
  });
}

// ==========================================
// CONSOLE SUPPRESSION FOR CLEANER TESTS
// ==========================================

// Suppress console.warn for known warnings in tests
const originalWarn = console.warn;
console.warn = (...args) => {
  const message = args[0];
  
  // Suppress specific warnings that are expected in tests
  const suppressWarnings = [
    'React Router Future Flag Warning',
    'validateDOMNesting',
    'Warning: An invalid form control',
    'Warning: componentWillReceiveProps',
    'Warning: componentWillMount',
  ];
  
  const shouldSuppress = suppressWarnings.some(warning => 
    typeof message === 'string' && message.includes(warning)
  );
  
  if (!shouldSuppress) {
    originalWarn.apply(console, args);
  }
};

// Suppress console.error for known errors in tests
const originalError = console.error;
console.error = (...args) => {
  const message = args[0];
  
  // Suppress specific errors that are expected in tests
  const suppressErrors = [
    'Warning: ReactDOM.render is no longer supported',
    'Warning: act(...) is not supported in production',
    'Warning: You are using the "console" shim',
  ];
  
  const shouldSuppress = suppressErrors.some(error => 
    typeof message === 'string' && message.includes(error)
  );
  
  if (!shouldSuppress) {
    originalError.apply(console, args);
  }
};

// ==========================================
// TEST UTILITIES
// ==========================================

// Helper function to wait for async operations
export const waitFor = (callback: () => void, options = { timeout: 1000 }) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      try {
        callback();
        resolve(undefined);
      } catch (error) {
        if (Date.now() - startTime >= options.timeout) {
          reject(error);
        } else {
          setTimeout(check, 50);
        }
      }
    };
    
    check();
  });
};

// Helper to mock API responses
export const mockApiResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
  });
};