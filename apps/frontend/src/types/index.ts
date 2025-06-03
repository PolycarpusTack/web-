// Central export for all types in Web+ Application

import type { ReactNode, ComponentType } from 'react';

// Use api-definitions as the single source of truth for API types
export * from './api-definitions';

// Export auth-specific types that aren't in api-definitions
export type { AuthContextType, LoginFormData, RegisterFormData } from './auth';

// UI component types
export * from './ui';

// Create aliases for backward compatibility and convenience
export type {
  User,
  Model,
  Conversation,
  Message,
  File as FileInfo,
  Pipeline,
  PipelineStep,
  AuthTokenResponse as AuthTokens,
  LoginRequest,
  UserRegistrationRequest as RegisterRequest,
  ChatCompletionRequest,
  ChatCompletionResponse
} from './api-definitions';

// Re-export common React types for convenience
export type {
  ReactNode,
  ReactElement,
  ComponentProps,
  ComponentPropsWithoutRef,
  ComponentPropsWithRef,
  ElementType,
  HTMLAttributes,
  RefObject,
  MutableRefObject,
  ForwardedRef,
  Ref,
} from 'react';

// Re-export common React Router types if needed
export type {
  NavigateFunction,
  Location,
  URLSearchParamsInit,
} from 'react-router-dom';

// Utility types for better TypeScript experience
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type DeepRequired<T> = {
  [P in keyof T]-?: T[P] extends object ? DeepRequired<T[P]> : T[P];
};

export type KeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? K : never;
}[keyof T];

export type Writable<T> = {
  -readonly [P in keyof T]: T[P];
};

export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Common generic types
export type Awaited<T> = T extends PromiseLike<infer U> ? U : T;

export type NonEmptyArray<T> = [T, ...T[]];

export type StringLiteral<T> = T extends string ? (string extends T ? never : T) : never;

export type NumberLiteral<T> = T extends number ? (number extends T ? never : T) : T;

// Type guards
export const isString = (value: unknown): value is string => typeof value === 'string';

export const isNumber = (value: unknown): value is number => typeof value === 'number' && !isNaN(value);

export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';

export const isObject = (value: unknown): value is Record<string, unknown> => 
  typeof value === 'object' && value !== null && !Array.isArray(value);

export const isArray = <T>(value: unknown): value is T[] => Array.isArray(value);

export const isFunction = (value: unknown): value is (...args: any[]) => any => typeof value === 'function';

export const isDefined = <T>(value: T | undefined | null): value is T => 
  value !== undefined && value !== null;

export const isEmpty = (value: unknown): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

// Environment types
export interface Environment {
  NODE_ENV: 'development' | 'production' | 'test';
  VITE_API_BASE_URL?: string;
  VITE_WS_URL?: string;
  VITE_ENABLE_DEVTOOLS?: string;
  VITE_LOG_LEVEL?: 'debug' | 'info' | 'warn' | 'error';
}

// Error boundary types
export interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ComponentType<{ error: Error; errorInfo: ErrorInfo; retry: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

// Performance monitoring types
export interface PerformanceMetrics {
  renderTime: number;
  loadTime: number;
  interactionTime?: number;
  memoryUsage?: number;
  apiCallDuration?: Record<string, number>;
}

export interface PerformanceEntry {
  name: string;
  startTime: number;
  duration: number;
  entryType: string;
}

// Feature flag types
export interface FeatureFlags {
  enableChat: boolean;
  enableFileUpload: boolean;
  enablePipelines: boolean;
  enableAdvancedModels: boolean;
  enableCollaboration: boolean;
  enableAnalytics: boolean;
  debugMode: boolean;
}

// Analytics types
export interface AnalyticsEvent {
  event: string;
  properties?: Record<string, any>;
  timestamp?: Date;
  userId?: string;
  sessionId?: string;
}

export interface AnalyticsProvider {
  track: (event: AnalyticsEvent) => void;
  identify: (userId: string, traits?: Record<string, any>) => void;
  page: (name: string, properties?: Record<string, any>) => void;
  reset: () => void;
}

// Internationalization types
export interface LocaleConfig {
  code: string;
  name: string;
  flag?: string;
  rtl?: boolean;
}

export interface TranslationKeys {
  [key: string]: string | TranslationKeys;
}

export interface I18nContext {
  locale: string;
  setLocale: (locale: string) => void;
  t: (key: string, variables?: Record<string, any>) => string;
  availableLocales: LocaleConfig[];
}

// Theme types (extended)
export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  foreground: string;
  muted: string;
  border: string;
  input: string;
  ring: string;
  destructive: string;
  success: string;
  warning: string;
  info: string;
}

export interface ThemeConfig {
  colors: {
    light: ThemeColors;
    dark: ThemeColors;
  };
  fonts: {
    sans: string[];
    mono: string[];
  };
  breakpoints: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  spacing: Record<string, string>;
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
  animations: Record<string, string>;
}

// Theme mode type
export type ThemeMode = 'light' | 'dark' | 'system';

// Global state types
export interface GlobalState {
  user: import('./api-definitions').User | null;
  theme: ThemeMode;
  locale: string;
  featureFlags: FeatureFlags;
  notifications: Notification[];
  loading: Record<string, boolean>;
  errors: Record<string, string>;
}

export interface GlobalAction {
  type: string;
  payload?: any;
}

export interface GlobalContextType {
  state: GlobalState;
  dispatch: (action: GlobalAction) => void;
}

// Plugin/Extension types (for future extensibility)
export interface Plugin {
  name: string;
  version: string;
  description?: string;
  author?: string;
  dependencies?: string[];
  hooks?: PluginHooks;
  components?: Record<string, ComponentType>;
  routes?: PluginRoute[];
}

export interface PluginHooks {
  onInit?: () => void;
  onDestroy?: () => void;
  onUserLogin?: (user: import('./api-definitions').User) => void;
  onUserLogout?: () => void;
  onRouteChange?: (route: string) => void;
}

export interface PluginRoute {
  path: string;
  component: ComponentType;
  exact?: boolean;
  protected?: boolean;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload?: any;
  timestamp: Date;
  id?: string;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export interface WebSocketContextType {
  connected: boolean;
  send: (message: WebSocketMessage) => void;
  subscribe: (type: string, handler: (payload: any) => void) => () => void;
  disconnect: () => void;
  reconnect: () => void;
}