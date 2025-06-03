// Authentication Types for Web+ Application

import { ReactNode } from 'react';
import { User, AuthTokens, JWTPayload } from './api';

export interface AuthContextType {
  // User state
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Auth actions
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshTokens: () => Promise<boolean>;
  clearError: () => void;

  // User profile actions
  updateProfile?: (data: Partial<User>) => Promise<boolean>;
  changePassword?: (oldPassword: string, newPassword: string) => Promise<boolean>;
}

export interface AuthProviderProps {
  children: ReactNode;
}

export interface LoginFormData {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  fullName?: string;
  acceptTerms: boolean;
}

export interface PasswordResetFormData {
  email: string;
}

export interface PasswordResetConfirmFormData {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ChangePasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ProfileUpdateFormData {
  username?: string;
  email?: string;
  fullName?: string;
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    notifications?: boolean;
    defaultModel?: string;
    language?: string;
  };
}

// Auth hook return types
export interface UseAuthReturn {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshTokens: () => Promise<boolean>;
  clearError: () => void;
  updateProfile?: (data: Partial<User>) => Promise<boolean>;
  changePassword?: (oldPassword: string, newPassword: string) => Promise<boolean>;
}

export interface UseLoginReturn {
  login: (data: LoginFormData) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export interface UseRegisterReturn {
  register: (data: RegisterFormData) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export interface UsePasswordResetReturn {
  requestReset: (email: string) => Promise<boolean>;
  confirmReset: (data: PasswordResetConfirmFormData) => Promise<boolean>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

// Protected route types
export interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  requireRoles?: string[];
  fallback?: ReactNode;
  redirectTo?: string;
}

export interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

// Role-based access types
export type UserRole = 'user' | 'admin' | 'developer' | 'moderator';

export interface RoleGuardProps {
  children: ReactNode;
  allowedRoles: UserRole[];
  fallback?: ReactNode;
  user?: User | null;
}

export interface PermissionGuardProps {
  children: ReactNode;
  permission: string;
  fallback?: ReactNode;
  user?: User | null;
}

// Auth API types
export interface AuthApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface RegisterResponse {
  user: User;
  message: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetResponse {
  message: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  password: string;
}

export interface PasswordResetConfirmResponse {
  message: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
}

export interface ProfileUpdateRequest {
  username?: string;
  email?: string;
  full_name?: string;
  preferences?: Record<string, any>;
}

export interface ProfileUpdateResponse {
  user: User;
  message: string;
}

export interface UserProfileResponse {
  user: User;
}

// Session management types
export interface SessionInfo {
  user: User;
  tokens: AuthTokens;
  expiresAt: Date;
  lastActivity: Date;
}

export interface SessionManagerOptions {
  tokenStorageKey?: string;
  refreshBeforeExpiry?: number; // minutes
  maxInactivity?: number; // minutes
  onSessionExpired?: () => void;
  onSessionRefreshed?: (tokens: AuthTokens) => void;
}

// Auth form validation types
export interface AuthFormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  fullName?: string;
  currentPassword?: string;
  newPassword?: string;
  general?: string;
}

export interface AuthFormTouched {
  username?: boolean;
  email?: boolean;
  password?: boolean;
  confirmPassword?: boolean;
  fullName?: boolean;
  currentPassword?: boolean;
  newPassword?: boolean;
}

export interface AuthFormState {
  values: Record<string, any>;
  errors: AuthFormErrors;
  touched: AuthFormTouched;
  isSubmitting: boolean;
  isValid: boolean;
}

// OAuth/Social auth types (for future use)
export interface SocialAuthProvider {
  id: string;
  name: string;
  icon?: ReactNode;
  color?: string;
  authUrl: string;
}

export interface SocialAuthResponse {
  provider: string;
  access_token: string;
  user: User;
}

// Two-factor authentication types (for future use)
export interface TwoFactorAuthSetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
}

export interface TwoFactorAuthVerifyRequest {
  code: string;
}

export interface TwoFactorAuthVerifyResponse {
  verified: boolean;
  backup_codes?: string[];
}

// API key management types
export interface ApiKeyCreateRequest {
  name: string;
  expires_in?: number; // days
  permissions?: string[];
}

export interface ApiKeyCreateResponse {
  key: string;
  id: string;
  name: string;
  expires_at?: string;
}

export interface ApiKeyListResponse {
  keys: Array<{
    id: string;
    name: string;
    created_at: string;
    expires_at?: string;
    last_used_at?: string;
    is_active: boolean;
  }>;
}

// Auth error types
export interface AuthError {
  type: 'validation' | 'authentication' | 'authorization' | 'network' | 'server';
  message: string;
  field?: string;
  code?: string;
}

export interface AuthErrorResponse {
  error: string;
  error_description?: string;
  error_uri?: string;
  details?: AuthError[];
}

// Auth configuration types
export interface AuthConfig {
  apiBaseUrl: string;
  loginEndpoint: string;
  registerEndpoint: string;
  refreshEndpoint: string;
  profileEndpoint: string;
  logoutEndpoint: string;
  tokenStorageKey: string;
  tokenPrefix: string;
  refreshTokenBeforeExpiry: number; // minutes
  maxSessionInactivity: number; // minutes
  enableRememberMe: boolean;
  enableRegistration: boolean;
  enablePasswordReset: boolean;
  enableSocialAuth: boolean;
  socialProviders: SocialAuthProvider[];
}

// Auth middleware types
export interface AuthMiddleware {
  name: string;
  execute: (request: Request) => Promise<Request>;
}

export interface AuthInterceptor {
  request?: (request: RequestInit) => Promise<RequestInit>;
  response?: (response: Response) => Promise<Response>;
  error?: (error: Error) => Promise<Error>;
}

// Auth storage types
export interface AuthStorage {
  getItem: (key: string) => Promise<string | null>;
  setItem: (key: string, value: string) => Promise<void>;
  removeItem: (key: string) => Promise<void>;
  clear: () => Promise<void>;
}

// Auth event types
export type AuthEventType = 
  | 'login'
  | 'logout'
  | 'register'
  | 'refresh'
  | 'profile_update'
  | 'password_change'
  | 'session_expired'
  | 'token_refresh_failed';

export interface AuthEvent {
  type: AuthEventType;
  user?: User;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface AuthEventListener {
  (event: AuthEvent): void;
}